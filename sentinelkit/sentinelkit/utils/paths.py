"""Path utilities shared across SentinelKit modules."""

from __future__ import annotations

from pathlib import Path

__all__ = ["normalize_path", "relative_to_root", "resolve_under_root"]


def normalize_path(value: str) -> str:
    """Normalize a repository-relative path to POSIX form."""

    cleaned = value.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    while "//" in cleaned:
        cleaned = cleaned.replace("//", "/")
    return cleaned or "."


def resolve_under_root(root: Path, target: Path | str) -> Path:
    """Resolve *target* under *root*."""

    root = root.resolve()
    path = Path(target)
    if not path.is_absolute():
        path = (root / path).resolve()
    return path


def relative_to_root(root: Path, target: Path) -> str:
    """Return POSIX-relative path."""

    return target.resolve().relative_to(root.resolve()).as_posix()
