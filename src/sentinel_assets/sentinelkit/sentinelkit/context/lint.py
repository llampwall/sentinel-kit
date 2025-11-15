"""Allowed Context linting utilities."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from pathlib import Path
from typing import Iterable, Literal, Sequence

from sentinelkit.context.allowed_context import (
    AllowedContextError,
    assert_include_exists,
    normalize_include,
)
from sentinelkit.context.limits import (
    CapsuleRule,
    ContextLimits,
    ContextLimitsError,
    ContextRule,
    load_context_limits,
)
from sentinelkit.utils.errors import SentinelKitError, build_error_payload
from sentinelkit.utils.paths import normalize_path

__all__ = ["Diagnostic", "LintSummary", "ContextLintError", "lint_context"]

Severity = Literal["error", "warning"]


@dataclass(slots=True, frozen=True)
class Diagnostic:
    """Context lint diagnostic entry."""

    path: str
    code: str
    message: str
    severity: Severity

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "code": self.code,
            "message": self.message,
            "severity": self.severity,
        }


@dataclass(slots=True, frozen=True)
class LintSummary:
    """Aggregated lint results."""

    checked_files: int
    diagnostics: tuple[Diagnostic, ...]
    strict: bool

    @property
    def errors(self) -> int:
        return sum(1 for diag in self.diagnostics if diag.severity == "error")

    @property
    def warnings(self) -> int:
        return sum(1 for diag in self.diagnostics if diag.severity == "warning")

    def should_fail(self) -> bool:
        return self.errors > 0 or (self.strict and self.warnings > 0)

    def to_dict(self) -> dict[str, object]:
        return {
            "checkedFiles": self.checked_files,
            "strict": self.strict,
            "errors": self.errors,
            "warnings": self.warnings,
            "diagnostics": [diag.to_dict() for diag in self.diagnostics],
        }

    def to_json(self, *, indent: int | None = None) -> str:
        payload = self.to_dict()
        payload["ok"] = not self.should_fail()
        return json.dumps(payload, indent=indent)


class ContextLintError(SentinelKitError):
    """Raised when the linter cannot run."""


@dataclass(slots=True)
class _ArtifactTarget:
    rule: ContextRule
    path: Path
    relative_path: str
    max_lines: int


def lint_context(
    *,
    capsules: Sequence[str | Path] | None = None,
    strict: bool = False,
    root: Path | str | None = None,
    config_path: Path | str | None = None,
    schema_path: Path | str | None = None,
) -> LintSummary:
    """Run the context linter and return diagnostics."""

    repo_root = _resolve_root(root)
    try:
        limits = load_context_limits(
            root=repo_root,
            config_path=config_path,
            schema_path=schema_path,
        )
    except ContextLimitsError as error:
        raise ContextLintError(error.payload) from error

    include_filter = _normalize_include_filter(repo_root, capsules)
    targets = _collect_artifact_targets(repo_root, limits, include_filter)

    diagnostics: list[Diagnostic] = []
    for target in targets:
        diagnostics.extend(_evaluate_target(repo_root, target, limits))

    diagnostics.sort(key=lambda diag: (diag.path, diag.code))
    return LintSummary(
        checked_files=len(targets),
        diagnostics=tuple(diagnostics),
        strict=strict,
    )


def _resolve_root(root: Path | str | None) -> Path:
    if root is None:
        return _auto_repo_root()
    resolved = Path(root).resolve()
    return resolved


def _auto_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists() or (candidate / "pyproject.toml").exists():
            return candidate
    raise ContextLintError(
        build_error_payload(
            code="CONTEXT_LINT_ROOT",
            message="Unable to determine repository root for context linting.",
        )
    )


def _normalize_include_filter(
    root: Path,
    capsules: Sequence[str | Path] | None,
) -> set[str] | None:
    if not capsules:
        return None
    includes: set[str] = set()
    for raw in capsules:
        candidate = Path(raw)
        resolved = candidate if candidate.is_absolute() else (root / candidate)
        resolved = resolved.resolve()
        try:
            relative = resolved.relative_to(root)
        except ValueError as error:
            raise ContextLintError(
                build_error_payload(
                    code="CONTEXT_LINT_ESCAPE",
                    message="Capsule path must reside inside the repository root.",
                    details={"path": str(candidate)},
                )
            ) from error
        includes.add(relative.as_posix())
    return includes


def _collect_artifact_targets(
    root: Path,
    limits: ContextLimits,
    include_filter: set[str] | None,
) -> list[_ArtifactTarget]:
    targets: list[_ArtifactTarget] = []
    override_matchers = [
        (override, _build_matcher(override.pattern))
        for override in limits.overrides
    ]

    seen: set[str] = set()
    for rule in limits.artifacts:
        for pattern in rule.globs:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                relative = path.resolve().relative_to(root).as_posix()
                if include_filter and relative not in include_filter:
                    continue
                if relative in seen:
                    continue
                seen.add(relative)
                limit = _resolve_max_lines(relative, rule, limits, override_matchers)
                targets.append(
                    _ArtifactTarget(
                        rule=rule,
                        path=path.resolve(),
                        relative_path=relative,
                        max_lines=limit,
                    )
                )
    return targets


def _resolve_max_lines(
    relative_path: str,
    rule: ContextRule,
    limits: ContextLimits,
    overrides: list[tuple[CapsuleRule, re.Pattern[str]]],
) -> int:
    for override, matcher in overrides:
        if matcher.fullmatch(relative_path):
            if override.max_lines is not None:
                return override.max_lines
    return rule.max_lines or limits.default_max_lines


def _build_matcher(pattern: str) -> re.Pattern[str]:
    normalized = normalize_path(pattern)
    regex = re.escape(normalized)
    regex = regex.replace(r"\*\*", ".*")
    regex = regex.replace(r"\*", "[^/]*")
    regex = regex.replace(r"\?", "[^/]")
    return re.compile(f"^{regex}$")


def _evaluate_target(root: Path, target: _ArtifactTarget, limits: ContextLimits) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    try:
        content = target.path.read_text(encoding="utf-8")
    except OSError as error:
        diagnostics.append(
            Diagnostic(
                path=target.relative_path,
                code="READ_ERROR",
                message=str(error),
                severity="error",
            )
        )
        return diagnostics

    line_count = _count_lines(content)
    if line_count > target.max_lines:
        diagnostics.append(
            Diagnostic(
                path=target.relative_path,
                code="MAX_LINES",
                message=f"exceeds {target.max_lines} line budget ({line_count} lines)",
                severity="error",
            )
        )
    else:
        ratio = target.max_lines and (line_count / target.max_lines)
        if ratio and ratio >= limits.warning_threshold:
            diagnostics.append(
                Diagnostic(
                    path=target.relative_path,
                    code="NEAR_LIMIT",
                    message=f"at {ratio * 100:.1f}% of limit ({line_count}/{target.max_lines})",
                    severity="warning",
                )
            )

    if target.rule.enforce_allowed_context:
        entries = _extract_allowed_context(content)
        if not entries:
            diagnostics.append(
                Diagnostic(
                    path=target.relative_path,
                    code="MISSING_ALLOWED_CONTEXT",
                    message="Allowed Context section is missing or empty",
                    severity="error",
                )
            )
        else:
            diagnostics.extend(
                _validate_allowed_context(entries, root, limits.forbidden_paths, target.relative_path)
            )

    return diagnostics


def _extract_allowed_context(markdown: str) -> list[str]:
    section = _extract_section(markdown, "Allowed Context")
    if not section:
        return []
    entries: list[str] = []
    current: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if _is_list_prefix(line):
            if current:
                entries.append(" ".join(current).strip())
                current.clear()
            current.append(line.split(maxsplit=1)[1] if " " in line else "")
        else:
            if current:
                current.append(line)
    if current:
        entries.append(" ".join(current).strip())
    return [entry for entry in (entry.strip() for entry in entries) if entry]


def _is_list_prefix(line: str) -> bool:
    return bool(re.match(r"^([-*]|\d+\.)\s+.+", line))


def _extract_section(markdown: str, heading: str) -> str:
    pattern = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
    lines = markdown.splitlines()
    capturing = False
    depth = 0
    bucket: list[str] = []
    for raw_line in lines:
        match = pattern.match(raw_line)
        if match:
            title = match.group(2).strip().lower()
            hashes = len(match.group(1))
            if title == heading.lower():
                capturing = True
                depth = hashes
                continue
            if capturing and hashes <= depth:
                break
        if capturing:
            bucket.append(raw_line)
    return "\n".join(bucket).strip()


def _validate_allowed_context(
    entries: Iterable[str],
    root: Path,
    forbidden: Sequence[str],
    relative_path: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()
    for entry in entries:
        try:
            normalized = normalize_include(root, entry)
        except AllowedContextError as error:
            diagnostics.append(
                Diagnostic(
                    path=relative_path,
                    code="INVALID_INCLUDE",
                    message=f"{entry} -> {error}",
                    severity="error",
                )
            )
            continue
        try:
            assert_include_exists(root, normalized)
        except AllowedContextError as error:
            diagnostics.append(
                Diagnostic(
                    path=relative_path,
                    code="MISSING_INCLUDE",
                    message=f"{normalized} -> {error}",
                    severity="error",
                )
            )
            continue
        if _is_forbidden(normalized, forbidden):
            diagnostics.append(
                Diagnostic(
                    path=relative_path,
                    code="FORBIDDEN_INCLUDE",
                    message=f"{normalized} is listed in forbiddenPaths",
                    severity="error",
                )
            )
        if normalized in seen:
            diagnostics.append(
                Diagnostic(
                    path=relative_path,
                    code="DUPLICATE_INCLUDE",
                    message=f"{normalized} is duplicated",
                    severity="warning",
                )
            )
        seen.add(normalized)
    return diagnostics


def _is_forbidden(entry: str, forbidden: Sequence[str]) -> bool:
    return any(entry == path or entry.startswith(f"{path}/") for path in forbidden)


def _count_lines(content: str) -> int:
    if not content:
        return 0
    newline_count = content.count("\n")
    return newline_count if content.endswith("\n") else newline_count + 1
