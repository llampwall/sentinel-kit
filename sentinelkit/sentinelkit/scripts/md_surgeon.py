"""Markdown snippet synchronization utilities."""

from __future__ import annotations

import argparse
import io
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Sequence

from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = [
    "MarkdownSurgeonError",
    "synchronize_snippet",
    "main",
]

Mode = Literal["replace", "insert", "append"]


@dataclass(slots=True)
class SurgeonOptions:
    file: Path
    marker: str
    content_path: Path | None = None
    heading: str | None = None
    mode: Mode = "replace"
    backup: bool = True
    content: str | None = None


class MarkdownSurgeonError(SentinelKitError):
    """Raised when snippet synchronization fails."""


def synchronize_snippet(options: SurgeonOptions) -> None:
    """Synchronize a snippet into a Markdown document."""

    target = options.file.resolve()
    if not target.exists():
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.missing_target",
                message=f"Markdown target '{target}' does not exist.",
            )
        )

    snippet = _load_snippet(options).strip()
    if not snippet:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.empty_snippet",
                message="Snippet content is empty.",
            )
        )

    _ensure_balanced_fences(snippet, source="snippet")

    doc = _normalize_newlines(target.read_text(encoding="utf-8"))
    start_marker = f"<!-- {options.marker}:start -->"
    end_marker = f"<!-- {options.marker}:end -->"

    start_idx = doc.find(start_marker)
    end_idx = doc.find(end_marker)

    if options.backup:
        backup = target.with_suffix(f"{target.suffix}.bak")
        shutil.copyfile(target, backup)

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        if options.mode == "insert":
            raise MarkdownSurgeonError(
                build_error_payload(
                    code="md_surgeon.insert_existing",
                    message="Markers already exist; use replace mode.",
                )
            )
        doc = _replace_block(doc, start_idx, end_idx, start_marker, end_marker, snippet)
    elif options.heading:
        doc = _insert_after_heading(doc, options.heading, start_marker, end_marker, snippet)
    elif options.mode == "append":
        doc = _append_block(doc, start_marker, end_marker, snippet)
    else:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.no_markers",
                message="No existing markers; provide --heading or use append mode.",
            )
        )

    _ensure_balanced_fences(doc, source="document")
    _ensure_no_replacement_chars(doc)
    target.write_text(doc, encoding="utf-8", newline="\n")


def _load_snippet(options: SurgeonOptions) -> str:
    if options.content is not None:
        return _normalize_newlines(options.content)
    if options.content_path:
        try:
            return _normalize_newlines(options.content_path.read_text(encoding="utf-8"))
        except OSError as error:
            raise MarkdownSurgeonError(
                build_error_payload(
                    code="md_surgeon.read_snippet",
                    message=f"Unable to read snippet '{options.content_path}': {error}",
                )
            ) from error
    if sys.stdin.closed or sys.stdin.isatty():
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.stdin_missing",
                message="Provide snippet content via --content or pipe data to stdin.",
            )
        )
    buffer = sys.stdin.read()
    if not buffer:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.stdin_empty",
                message="Snippet content from stdin is empty.",
            )
        )
    return _normalize_newlines(buffer)


def _replace_block(
    doc: str,
    start_idx: int,
    end_idx: int,
    start_marker: str,
    end_marker: str,
    snippet: str,
) -> str:
    head = doc[:start_idx]
    tail = doc[end_idx + len(end_marker) :]
    return f"{head}{start_marker}\n{snippet}\n{end_marker}{tail}"


def _insert_after_heading(
    doc: str,
    heading: str,
    start_marker: str,
    end_marker: str,
    snippet: str,
) -> str:
    lines = doc.split("\n")
    heading_idx = _find_heading_index(lines, heading)
    if heading_idx is None:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.heading_missing",
                message=f'Heading "{heading}" not found.',
            )
        )
    insert_line = heading_idx + 1
    block = [start_marker, snippet, end_marker]
    block_lines = ["", *block, ""]
    new_lines = lines[:insert_line] + block_lines + lines[insert_line:]
    return "\n".join(new_lines)


def _append_block(doc: str, start_marker: str, end_marker: str, snippet: str) -> str:
    sep = "" if doc.endswith("\n") else "\n"
    return f"{doc}{sep}\n\n{start_marker}\n{snippet}\n{end_marker}\n"


def _find_heading_index(lines: Sequence[str], heading: str) -> int | None:
    trimmed = heading.strip().lower()
    for idx, line in enumerate(lines):
        if not line.startswith("#"):
            continue
        stripped = line.strip()
        if not stripped:
            continue
        hashes, _, title = stripped.partition(" ")
        if not hashes or not title:
            continue
        if 2 <= len(hashes) <= 6 and title.lower() == trimmed:
            return idx
    return None


def _normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")


def _ensure_balanced_fences(markdown: str, *, source: str) -> None:
    ticks = sum(1 for line in markdown.splitlines() if line.startswith("```"))
    tildes = sum(1 for line in markdown.splitlines() if line.startswith("~~~"))
    if ticks % 2 != 0 or tildes % 2 != 0:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.unbalanced_fence",
                message=f"{source} has unbalanced code fences.",
            )
        )


def _ensure_no_replacement_chars(markdown: str) -> None:
    if "\uFFFD" in markdown:
        raise MarkdownSurgeonError(
            build_error_payload(
                code="md_surgeon.replacement_char",
                message="Replacement character detected; check encoding.",
            )
        )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Synchronize Markdown snippets (md-surgeon).")
    parser.add_argument("--file", required=True, type=Path, help="Markdown file to update.")
    parser.add_argument("--marker", required=True, help="Marker identifier, e.g. SENTINEL:CAPSULES.")
    parser.add_argument("--content", type=Path, help="Path to snippet content (defaults to stdin).")
    parser.add_argument("--heading", help="Heading (H2-H6) to insert after when markers are missing.")
    parser.add_argument(
        "--mode",
        choices=("replace", "insert", "append"),
        default="replace",
        help="Insertion mode when markers are missing.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip writing a .bak backup before modifying the target file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    options = SurgeonOptions(
        file=args.file,
        marker=args.marker,
        content_path=args.content,
        heading=args.heading,
        mode=args.mode,
        backup=not args.no_backup,
    )

    try:
        synchronize_snippet(options)
    except MarkdownSurgeonError as error:
        print(f"md-surgeon: {error.payload.message}", file=sys.stderr)
        if error.payload.remediation:
            print(f"hint: {error.payload.remediation}", file=sys.stderr)
        return 1
    except Exception as error:  # pragma: no cover - safeguard
        print(f"md-surgeon: {error}", file=sys.stderr)
        return 1

    print(f"md-surgeon: ok -> {args.file.name} [marker={args.marker}]")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
