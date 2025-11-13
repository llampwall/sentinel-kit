"""Decision ledger core helpers used by the CLI namespace."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import subprocess
from pathlib import Path
from typing import Iterable

import portalocker

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = [
    "DecisionLedger",
    "DecisionLedgerError",
    "DecisionPayload",
    "LedgerAppendResult",
    "ProducedBySnippets",
]

ID_PATTERN = re.compile(r"^[A-Z]-\d{4}$")
NEXT_ID_BLOCK = re.compile(r"(## NEXT_ID\s*)(?:\r?\n)+([A-Z]-\d{4})")


class DecisionLedgerError(SentinelKitError):
    """Raised when ledger operations fail."""


@dataclass(slots=True)
class DecisionPayload:
    """User-supplied decision metadata prior to ID assignment."""

    author: str
    scope: str
    decision: str
    rationale: str
    outputs: Iterable[str]
    supersedes: str = "none"
    date_override: str | None = None


@dataclass(slots=True)
class ProducedBySnippets:
    """Represents ProducedBy header variations."""

    plain: str
    javascript: str
    python: str
    markdown: str


@dataclass(slots=True)
class LedgerAppendResult:
    """Structured result returned after appending to the ledger."""

    id: str
    entry: str
    ledger_path: Path
    wrote_ledger: bool
    dry_run: bool
    output_path: Path | None
    snippets: ProducedBySnippets


@dataclass(slots=True)
class _DecisionEntry:
    """Internal normalized ledger entry representation."""

    id: str
    date: str
    author: str
    scope: str
    decision: str
    rationale: str
    outputs: str
    supersedes: str

    def format(self) -> str:
        lines = [
            f"ID: {self.id}",
            f"Date: {self.date}",
            f"Author: {self.author}",
            f"Scope: {self.scope}",
            f"Decision: {self.decision}",
            f"Rationale: {self.rationale}",
            f"Outputs: {self.outputs}",
            f"Supersedes: {self.supersedes}",
        ]
        return "\n".join(lines)


class DecisionLedger:
    """Manage DECISIONS.md mutations with deterministic formatting + locking."""

    def __init__(self, ledger_path: Path | str, *, lock_timeout: float = 10.0) -> None:
        self.ledger_path = Path(ledger_path)
        self.lock_path = self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock")
        self.lock_timeout = lock_timeout

    def append(
        self,
        payload: DecisionPayload,
        *,
        agent: str | None = None,
        rules_hash: str | None = None,
        dry_run: bool = False,
        output_path: Path | None = None,
    ) -> LedgerAppendResult:
        if not self.ledger_path.exists():
            raise DecisionLedgerError(
                build_error_payload(
                    code="decision.ledger_missing",
                    message=f"Ledger '{self.ledger_path}' does not exist.",
                    remediation="Create DECISIONS.md or point --ledger at the correct path.",
                )
            )

        with portalocker.Lock(str(self.lock_path), timeout=self.lock_timeout, mode="w"):
            content = self.ledger_path.read_text(encoding="utf-8")
            current_id = _extract_next_id(content)
            _assert_id_unused(content, current_id)
            entry = _DecisionEntry(
                id=current_id,
                date=_normalize_date(payload.date_override),
                author=_require(payload.author, "author"),
                scope=_require(payload.scope, "scope"),
                decision=_require(payload.decision, "decision"),
                rationale=_require(payload.rationale, "rationale"),
                outputs=_normalize_outputs(payload.outputs),
                supersedes=_normalize_supersedes(payload.supersedes),
            )
            bumped = _bump_id(current_id)
            updated_content = _render_updated_ledger(content, bumped, entry.format())

            preview_path = None
            if output_path:
                preview_path = Path(output_path)
                preview_path.parent.mkdir(parents=True, exist_ok=True)
                preview_path.write_text(updated_content, encoding="utf-8", newline="\n")

            wrote_ledger = False
            if not dry_run:
                self.ledger_path.write_text(updated_content, encoding="utf-8", newline="\n")
                wrote_ledger = True

            agent_token = _normalize_agent(agent or payload.author)
            snippets = _build_snippets(
                agent=agent_token,
                rules_hash=rules_hash or f"{agent_token}@1.0",
                decision_id=current_id,
                git_hash=_git_short_hash(self.ledger_path.parent),
            )

            return LedgerAppendResult(
                id=current_id,
                entry=entry.format(),
                ledger_path=self.ledger_path,
                wrote_ledger=wrote_ledger,
                dry_run=dry_run,
                output_path=preview_path,
                snippets=snippets,
            )


def _extract_next_id(content: str) -> str:
    match = NEXT_ID_BLOCK.search(content)
    if not match:
        raise DecisionLedgerError(
            build_error_payload(
                code="decision.missing_next_id",
                message="NEXT_ID block not found in DECISIONS.md",
            )
        )
    return match.group(2)


def _assert_id_unused(content: str, decision_id: str) -> None:
    pattern = re.compile(rf"^ID:\s*{re.escape(decision_id)}\s*$", re.MULTILINE)
    if pattern.search(content):
        raise DecisionLedgerError(
            build_error_payload(
                code="decision.duplicate_id",
                message=f"Decision {decision_id} already exists in the ledger.",
                remediation="Update NEXT_ID to an unused value or archive old entries.",
            )
        )


def _bump_id(decision_id: str) -> str:
    if not ID_PATTERN.match(decision_id):
        raise DecisionLedgerError(
            build_error_payload(code="decision.invalid_id", message=f"Invalid decision id '{decision_id}'.")
        )
    prefix, _, number = decision_id.partition("-")
    next_value = str(int(number) + 1).zfill(4)
    return f"{prefix}-{next_value}"


def _normalize_outputs(outputs: Iterable[str]) -> str:
    tokens: list[str] = []
    for entry in outputs:
        if entry is None:
            continue
        tokens.extend(filter(None, (part.strip() for part in str(entry).split(","))))
    if not tokens:
        raise DecisionLedgerError(
            build_error_payload(
                code="decision.missing_outputs",
                message="At least one output path is required.",
            )
        )
    return ", ".join(tokens)


def _normalize_supersedes(value: str | None) -> str:
    return value.strip() if value and value.strip() else "none"


def _normalize_date(date_override: str | None) -> str:
    if date_override:
        return date_override.strip()
    return date.today().isoformat()


def _require(value: str, label: str) -> str:
    if value is None:
        raise DecisionLedgerError(
            build_error_payload(code="decision.missing_field", message=f"Missing required value '{label}'.")
        )
    trimmed = value.strip()
    if not trimmed:
        raise DecisionLedgerError(
            build_error_payload(code="decision.missing_field", message=f"Missing required value '{label}'.")
        )
    return trimmed


def _render_updated_ledger(content: str, next_id: str, entry: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        block = match.group(0)
        separator = "\r\n" if "\r\n" in block else "\n"
        return f"{match.group(1).rstrip()}{separator}{next_id}"

    replaced, count = NEXT_ID_BLOCK.subn(_replace, content, count=1)
    if count == 0:
        raise DecisionLedgerError(
            build_error_payload(
                code="decision.missing_next_id",
                message="Unable to update NEXT_ID block.",
            )
        )
    return f"{replaced.rstrip()}\n\n{entry}\n"


def _normalize_agent(agent: str) -> str:
    return agent.strip().upper()


def _git_short_hash(cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(cwd),
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except OSError:
        pass
    return "unknown"


def _build_snippets(*, agent: str, rules_hash: str, decision_id: str, git_hash: str) -> ProducedBySnippets:
    plain = f"ProducedBy={agent} RulesHash={rules_hash} Decision={decision_id} (#{git_hash})"
    return ProducedBySnippets(
        plain=plain,
        javascript=f"/* {plain} */",
        python=f"# {plain}",
        markdown=f"<!-- {plain} -->",
    )
