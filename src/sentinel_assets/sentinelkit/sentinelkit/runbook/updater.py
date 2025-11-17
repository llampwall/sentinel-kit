"""Structured IMPLEMENTATION.md runbook updates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = ["RunbookSection", "RunbookUpdateResult", "RunbookUpdater"]


@dataclass(slots=True)
class RunbookSection:
    """Metadata describing a managed runbook section."""

    slug: str
    title: str
    description: str

    @property
    def heading(self) -> str:
        return f"## {self.title}"

    @property
    def placeholder(self) -> str:
        return f"- _No entries yet. Use `sentinel runbook append --section {self.slug} --note ...`_"


@dataclass(slots=True)
class RunbookUpdateResult:
    """Details about an applied (or previewed) runbook update."""

    section: RunbookSection
    path: Path
    timestamp: str
    author: str
    note: str
    wrote_file: bool
    dry_run: bool
    output_path: Path | None
    content: str


class RunbookUpdaterError(SentinelKitError):
    """Raised when runbook updates fail."""


SECTION_ORDER: tuple[RunbookSection, ...] = (
    RunbookSection(
        slug="enforcement",
        title="Current Enforcement Surface",
        description="Tracks Sentinel gates, CLIs, and guardrails that are active today.",
    ),
    RunbookSection(
        slug="flow",
        title="Execution Flow",
        description="Summaries of how Spec-Kit + SentinelKit run in practice (bootstrap, slash commands, automation).",
    ),
    RunbookSection(
        slug="gaps",
        title="Known Gaps",
        description="Outstanding risks, TODOs, or regressions the team is tracking.",
    ),
    RunbookSection(
        slug="ci",
        title="CI Workflow",
        description="Notes about workflows, required gates, and cross-platform nuances.",
    ),
    RunbookSection(
        slug="stack",
        title="Stack Context",
        description="Language/runtime/framework choices and why they were made.",
    ),
)

SECTION_REGISTRY = {section.slug: section for section in SECTION_ORDER}

DEFAULT_RUNBOOK_HEADER = "# Implementation Notes"


class RunbookUpdater:
    """Append structured notes to IMPLEMENTATION.md sections."""

    def __init__(self, path: Path | str = Path(".sentinel/docs/IMPLEMENTATION.md")) -> None:
        self.path = Path(path)

    def append(
        self,
        *,
        section: str,
        note: str,
        author: str,
        timestamp: datetime | None = None,
        dry_run: bool = False,
        output_path: Path | str | None = None,
    ) -> RunbookUpdateResult:
        target = _get_section(section)
        normalized_note = _normalize_text(note, "note")
        normalized_author = _normalize_text(author, "author")
        timestamp_value = timestamp or datetime.now(timezone.utc)
        timestamp_str = timestamp_value.strftime("%Y-%m-%d %H:%MZ")

        content = self._read_or_initialize()
        ensured = _ensure_sections(content)
        updated = _insert_note(
            ensured,
            section=target,
            note_line=_format_note(timestamp_str, normalized_author, normalized_note),
        )

        preview_path: Path | None = None
        if output_path:
            preview_path = Path(output_path)
            preview_path.parent.mkdir(parents=True, exist_ok=True)
            preview_path.write_text(updated, encoding="utf-8", newline="\n")

        wrote_file = False
        if not dry_run:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(updated, encoding="utf-8", newline="\n")
            wrote_file = True

        return RunbookUpdateResult(
            section=target,
            path=self.path,
            timestamp=timestamp_str,
            author=normalized_author,
            note=normalized_note,
            wrote_file=wrote_file,
            dry_run=dry_run,
            output_path=preview_path,
            content=updated,
        )

    def _read_or_initialize(self) -> str:
        if self.path.exists():
            return self.path.read_text(encoding="utf-8")
        return f"{DEFAULT_RUNBOOK_HEADER}\n"


def _get_section(slug: str) -> RunbookSection:
    normalized = slug.lower().strip()
    if normalized not in SECTION_REGISTRY:
        raise RunbookUpdaterError(
            build_error_payload(
                code="runbook.unknown_section",
                message=f"Unknown runbook section '{slug}'.",
                remediation=f"Choose one of: {', '.join(SECTION_REGISTRY)}",
            )
        )
    return SECTION_REGISTRY[normalized]


def _normalize_text(value: str, label: str) -> str:
    if value is None:
        raise RunbookUpdaterError(
            build_error_payload(code="runbook.missing_field", message=f"Missing required {label}.")
        )
    collapsed = " ".join(chunk for chunk in " ".join(value.splitlines()).split(" ") if chunk)
    if not collapsed:
        raise RunbookUpdaterError(
            build_error_payload(code="runbook.missing_field", message=f"Missing required {label}.")
        )
    return collapsed


def _ensure_sections(content: str) -> str:
    lines = content.splitlines()
    if not lines:
        lines = [DEFAULT_RUNBOOK_HEADER, ""]
    elif not lines[0].startswith("# "):
        lines.insert(0, DEFAULT_RUNBOOK_HEADER)
        lines.insert(1, "")

    insertion_idx = _find_first_heading_index(lines)
    for section in SECTION_ORDER:
        if section.heading in lines:
            continue
        block = _build_section_block(section)
        lines[insertion_idx:insertion_idx] = block
        insertion_idx += len(block)
    return _normalize_lines(lines)


def _find_first_heading_index(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if line.startswith("## "):
            return idx
    return len(lines)


def _build_section_block(section: RunbookSection) -> list[str]:
    return [
        "",
        section.heading,
        "",
        f"> {section.description}",
        "",
        section.placeholder,
        "",
    ]


def _insert_note(content: str, *, section: RunbookSection, note_line: str) -> str:
    lines = content.splitlines()
    try:
        start = lines.index(section.heading)
    except ValueError as exc:  # pragma: no cover - ensured earlier
        raise RunbookUpdaterError(
            build_error_payload(
                code="runbook.missing_section",
                message=f"Section '{section.title}' was not initialized.",
            )
        ) from exc
    end = _find_section_end(lines, start)

    body = lines[start + 1 : end]
    placeholder = section.placeholder.strip()
    cleaned: list[str] = [line for line in body if line.strip() != placeholder]

    while cleaned and cleaned[-1].strip() == "":
        cleaned.pop()
    cleaned.append("")
    cleaned.append(note_line)
    cleaned.append("")

    lines[start + 1 : end] = cleaned
    return _normalize_lines(lines)


def _find_section_end(lines: list[str], start: int) -> int:
    for idx in range(start + 1, len(lines)):
        line = lines[idx]
        if line.startswith("## "):
            return idx
    return len(lines)


def _format_note(timestamp: str, author: str, note: str) -> str:
    return f"- [{timestamp}] ({author}) {note}"


def _normalize_lines(lines: Iterable[str]) -> str:
    text = "\n".join(lines)
    return text.rstrip() + "\n"
