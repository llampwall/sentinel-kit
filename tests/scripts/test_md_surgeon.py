"""Tests for the Python md-surgeon replacement."""

from __future__ import annotations

from pathlib import Path

import pytest

from sentinelkit.scripts.md_surgeon import (
    MarkdownSurgeonError,
    SurgeonOptions,
    main as md_surgeon_main,
    synchronize_snippet,
)


def test_replace_existing_block(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text(
        "\n".join(
            [
                "# Doc",
                "<!-- SENTINEL:TEST:start -->",
                "old",
                "<!-- SENTINEL:TEST:end -->",
                "tail",
            ]
        ),
        encoding="utf-8",
    )
    snippet = tmp_path / "snippet.md"
    snippet.write_text("new snippet\n```bash\nuv run sentinel\n```", encoding="utf-8")

    synchronize_snippet(
        SurgeonOptions(file=target, marker="SENTINEL:TEST", content_path=snippet)
    )

    updated = target.read_text(encoding="utf-8")
    assert "old" not in updated
    assert "uv run sentinel" in updated
    assert (tmp_path / "doc.md.bak").exists()


def test_insert_after_heading_when_markers_missing(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Doc\n## Section\nContent\n", encoding="utf-8")

    synchronize_snippet(
        SurgeonOptions(
            file=target,
            marker="SENTINEL:TEST",
            heading="Section",
            content="Inserted block",
        )
    )

    updated = target.read_text(encoding="utf-8")
    assert "Inserted block" in updated
    assert updated.count("SENTINEL:TEST:start") == 1


def test_append_mode_appends_to_document(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Doc\nContent", encoding="utf-8")
    synchronize_snippet(
        SurgeonOptions(
            file=target,
            marker="SENTINEL:TEST",
            mode="append",
            content="appended",
        )
    )
    updated = target.read_text(encoding="utf-8")
    assert updated.rstrip().endswith("<!-- SENTINEL:TEST:end -->")


def test_unbalanced_snippet_raises(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Doc\nContent", encoding="utf-8")
    snippet = tmp_path / "snippet.md"
    snippet.write_text("```\nunbalanced fence", encoding="utf-8")
    with pytest.raises(MarkdownSurgeonError):
        synchronize_snippet(
            SurgeonOptions(file=target, marker="SENTINEL:TEST", content_path=snippet)
        )


def test_cli_main_reports_failures(tmp_path: Path) -> None:
    target = tmp_path / "doc.md"
    target.write_text("# Doc\nContent", encoding="utf-8")
    exit_code = md_surgeon_main(
        [
            "--file",
            str(target),
            "--marker",
            "SENTINEL:TEST",
        ]
    )
    assert exit_code == 1

