"""Fail if Node/pnpm artifacts reappear in the Python-only workspace."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
BANNED_TEXT_ROOTS = {
    ROOT / "README.md",
    ROOT / "SUPPORT.md",
    ROOT / "docs",
    ROOT / ".github/pull_request_template.md",
    ROOT / ".sentinel/snippets/workflow-badge.md",
}
TEXT_EXTENSIONS = {
    ".md",
    ".markdown",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".txt",
    ".ini",
    ".cfg",
}
BANNED_KEYWORDS = ["pnpm", "node_modules", ".sentinel/package.json", ".sentinel/node_modules", "vitest"]
BANNED_FILES = [
    ROOT / "pnpm-lock.yaml",
    ROOT / "pnpm-workspace.yaml",
    ROOT / ".sentinel" / "package.json",
    ROOT / ".sentinel" / "vitest.config.ts",
    ROOT / ".sentinel" / "vitest.config.sentinel.ts",
    ROOT / ".sentinel" / "tsconfig.json",
    ROOT / ".sentinel" / "eslint.config.js",
]


def main() -> None:
    errors: list[str] = []

    for candidate in BANNED_FILES:
        if candidate.exists():
            errors.append(f"Found forbidden artifact: {candidate.relative_to(ROOT)}")

    for path in iter_text_files():
        content = read_text(path)
        for keyword in BANNED_KEYWORDS:
            if keyword in content:
                rel = path.relative_to(ROOT)
                errors.append(f"Keyword '{keyword}' found in {rel}")

    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)


def iter_text_files() -> Iterable[Path]:
    for root in BANNED_TEXT_ROOTS:
        yield from _iter_text_under(root)


def _iter_text_under(root: Path) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTENSIONS:
            yield root
        return
    if not root.exists():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


if __name__ == "__main__":
    main()
