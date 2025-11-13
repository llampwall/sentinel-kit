"""Allowed Context discovery + helpers for SentinelKit."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = [
    "AllowedContextEntry",
    "AllowedContextError",
    "discover_allowed_context",
    "build_allowed_context",
    "normalize_include",
    "assert_include_exists",
]

DEFAULT_CONTEXT_DIR = Path(".sentinel/context")
EXCLUDED_SUBPATHS = frozenset({"limits"})
GLOB_MARKERS = frozenset({"*", "?", "["})


@dataclass(slots=True, frozen=True)
class AllowedContextEntry:
    """Normalized Allowed Context item with deterministic ordering."""

    relative_path: str
    absolute_path: Path
    line_count: int
    is_glob: bool = False

    def to_dict(self) -> dict[str, str | int | bool]:
        """Serialize the entry for JSON output."""
        return {
            "path": self.relative_path,
            "absolute": str(self.absolute_path),
            "lineCount": self.line_count,
            "isGlob": self.is_glob,
        }


class AllowedContextError(SentinelKitError):
    """Raised when Allowed Context operations fail."""


def discover_allowed_context(
    paths: Sequence[str] | None = None,
    *,
    root: Path | str | None = None,
    context_dir: Path | str | None = None,
) -> list[AllowedContextEntry]:
    """Return deterministic Allowed Context entries (context docs + optional seeds).

    Parameters
    ----------
    paths:
        Additional Allowed Context entries requested by a capsule or CLI flag.
    root:
        Repository root. Defaults to auto-discovery from this module location.
    context_dir:
        Directory containing shared context docs relative to the repo root.
    """

    repo_root = _resolve_root(root)
    context_root = _resolve_context_dir(repo_root, context_dir)
    defaults = _list_context_relpaths(repo_root, context_root)

    merged: dict[str, AllowedContextEntry] = {}
    for relative in defaults:
        entry = _build_entry(repo_root, relative)
        merged[relative] = entry

    for raw in paths or []:
        normalized = normalize_include(repo_root, raw)
        assert_include_exists(repo_root, normalized)
        entry = _build_entry(repo_root, normalized)
        merged.setdefault(normalized, entry)

    return [merged[key] for key in sorted(merged)]


def build_allowed_context(
    *,
    seeds: Sequence[str] | None = None,
    root: Path | str | None = None,
    context_dir: Path | str | None = None,
) -> list[str]:
    """Return a sorted Allowed Context list (paths only)."""

    entries = discover_allowed_context(seeds, root=root, context_dir=context_dir)
    return [entry.relative_path for entry in entries]


def normalize_include(root: Path | str, raw: str) -> str:
    """Normalize a user-provided Allowed Context expression."""

    if not raw or not isinstance(raw, str):
        raise AllowedContextError(
            build_error_payload(
                code="ALLOWED_CONTEXT_INVALID",
                message="Allowed Context entry must be a non-empty string",
            )
        )

    cleaned = raw.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    while "//" in cleaned:
        cleaned = cleaned.replace("//", "/")
    if not cleaned:
        raise AllowedContextError(
            build_error_payload(
                code="ALLOWED_CONTEXT_INVALID",
                message="Allowed Context entry cannot be empty",
            )
        )

    root_path = _resolve_root(root)
    base = _glob_base(cleaned)
    resolved_base = (root_path / base).resolve()
    if not _is_within_root(root_path, resolved_base):
        raise AllowedContextError(
            build_error_payload(
                code="ALLOWED_CONTEXT_ESCAPE",
                message="Allowed Context entry escapes the repository root",
                details={"entry": raw},
            )
        )

    return cleaned


def assert_include_exists(root: Path | str, normalized: str) -> None:
    """Ensure an Allowed Context entry references an existing path."""

    root_path = _resolve_root(root)
    target = _glob_base(normalized)
    if target in ("", "."):
        return
    resolved = (root_path / target).resolve()
    if not resolved.exists():
        raise AllowedContextError(
            build_error_payload(
                code="ALLOWED_CONTEXT_MISSING",
                message="Allowed Context entry does not exist",
                details={"entry": normalized},
            )
        )


def _resolve_root(root: Path | str | None) -> Path:
    if root is None:
        return _auto_repo_root()
    root_path = Path(root).resolve()
    return root_path


def _auto_repo_root() -> Path:
    current = Path(__file__).resolve().parent
    for candidate in (current, *current.parents):
        root_marker = candidate / ".git"
        pyproject_marker = candidate / "pyproject.toml"
        if root_marker.exists() or pyproject_marker.exists():
            return candidate
    raise AllowedContextError(
        build_error_payload(
            code="ALLOWED_CONTEXT_ROOT",
            message="Unable to determine repository root for Allowed Context discovery",
        )
    )


def _resolve_context_dir(root: Path, context_dir: Path | str | None) -> Path:
    rel = context_dir if context_dir is not None else DEFAULT_CONTEXT_DIR
    candidate = (root / rel).resolve()
    if not _is_within_root(root, candidate):
        raise AllowedContextError(
            build_error_payload(
                code="ALLOWED_CONTEXT_CONTEXT_DIR",
                message="Context directory escapes repository root",
                details={"directory": str(rel)},
            )
        )
    return candidate


def _list_context_relpaths(root: Path, context_root: Path) -> list[str]:
    if not context_root.exists() or not context_root.is_dir():
        return []

    entries: list[Path] = []

    def walk(directory: Path) -> None:
        try:
            dir_entries = list(directory.iterdir())
        except OSError:
            return
        for entry in dir_entries:
            if entry.is_dir():
                relative = _posix_relative(entry, context_root)
                top_level = relative.split("/", 1)[0] if relative else entry.name
                if top_level in EXCLUDED_SUBPATHS:
                    continue
                walk(entry)
            elif entry.is_file():
                entries.append(entry)

    walk(context_root)
    rel_paths = [_posix_relative(path, root) for path in entries]
    return sorted(rel_paths)


def _build_entry(root: Path, relative: str) -> AllowedContextEntry:
    has_glob = _has_glob(relative)
    if has_glob:
        base = _glob_base(relative)
        try:
            absolute = (root / base).resolve()
        except FileNotFoundError as error:
            raise AllowedContextError(
                build_error_payload(
                    code="ALLOWED_CONTEXT_BASE_MISSING",
                    message=f"Base path '{base}' does not exist for pattern '{relative}'",
                )
            ) from error
        if not _is_within_root(root, absolute):
            raise AllowedContextError(
                build_error_payload(
                    code="ALLOWED_CONTEXT_ESCAPE",
                    message=f"Allowed Context entry '{relative}' escapes repository root",
                )
            )
        line_count = 0
    else:
        try:
            absolute = (root / relative).resolve()
        except FileNotFoundError as error:
            raise AllowedContextError(
                build_error_payload(
                    code="ALLOWED_CONTEXT_MISSING",
                    message=f"Allowed Context entry '{relative}' does not exist",
                )
            ) from error
        if not _is_within_root(root, absolute):
            raise AllowedContextError(
                build_error_payload(
                    code="ALLOWED_CONTEXT_ESCAPE",
                    message=f"Allowed Context entry '{relative}' escapes repository root",
                )
            )
        try:
            if absolute.is_file():
                line_count = _count_lines(absolute)
            else:
                line_count = 0
        except OSError as error:
            raise AllowedContextError(
                build_error_payload(
                    code="ALLOWED_CONTEXT_READ",
                    message=f"Unable to read '{relative}': {error}",
                )
            ) from error
    return AllowedContextEntry(
        relative_path=relative,
        absolute_path=absolute,
        line_count=line_count,
        is_glob=has_glob,
    )


def _count_lines(path: Path) -> int:
    try:
        text = path.read_text(encoding="utf-8")
        if not text:
            return 0
        return text.count("\n") + 1
    except UnicodeDecodeError:
        data = path.read_bytes()
        if not data:
            return 0
        return data.count(b"\n") + 1


def _glob_base(pattern: str) -> str:
    if not _has_glob(pattern):
        return pattern or "."
    idx = min(
        (pattern.index(marker) for marker in GLOB_MARKERS if marker in pattern),
        default=len(pattern),
    )
    base = pattern[:idx]
    return base.rstrip("/") or "."


def _has_glob(pattern: str) -> bool:
    return any(marker in pattern for marker in GLOB_MARKERS)


def _is_within_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def _posix_relative(path: Path, start: Path) -> str:
    return path.relative_to(start).as_posix()
