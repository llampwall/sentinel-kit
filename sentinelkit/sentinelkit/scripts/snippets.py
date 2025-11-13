"""Snippet synchronization helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from sentinelkit.scripts.md_surgeon import SurgeonOptions, synchronize_snippet
from sentinelkit.utils.errors import SentinelKitError, build_error_payload

__all__ = ["SnippetMapping", "sync_snippets", "DEFAULT_SNIPPETS"]


class SnippetSyncError(SentinelKitError):
    """Raised when snippet synchronization fails."""


@dataclass(slots=True)
class SnippetMapping:
    marker: str
    target: Path
    snippet: Path
    heading: str | None = None
    mode: str = "replace"


DEFAULT_SNIPPETS: tuple[SnippetMapping, ...] = (
    SnippetMapping(
        marker="SENTINEL:WORKFLOW-BADGE",
        target=Path("README.md"),
        snippet=Path(".sentinel/snippets/workflow-badge.md"),
    ),
    SnippetMapping(
        marker="SENTINEL:MCP-CONTRACT-VALIDATE",
        target=Path("README.md"),
        snippet=Path(".sentinel/snippets/mcp-contract-validate.md"),
    ),
    SnippetMapping(
        marker="SENTINEL:CAPSULES",
        target=Path("README.md"),
        snippet=Path(".sentinel/snippets/capsules.md"),
    ),
    SnippetMapping(
        marker="SENTINEL:DECISION-LOG",
        target=Path("README.md"),
        snippet=Path(".sentinel/snippets/decision-log.md"),
    ),
    SnippetMapping(
        marker="SENTINEL:UPSTREAM-DECISION",
        target=Path("UPSTREAM.md"),
        snippet=Path(".sentinel/snippets/upstream-decision.md"),
    ),
    SnippetMapping(
        marker="SENTINEL:PROMPT-RENDER",
        target=Path("README.md"),
        snippet=Path(".sentinel/snippets/prompt-render.md"),
        heading="Prompt renderer workflow",
    ),
)


def sync_snippets(
    *,
    root: Path | str,
    mappings: Sequence[SnippetMapping] = DEFAULT_SNIPPETS,
    markers: Iterable[str] | None = None,
) -> list[Path]:
    """Synchronize documentation snippets using md-surgeon."""

    root_path = Path(root).resolve()
    selected = {marker.upper() for marker in (markers or [])}
    touched: list[Path] = []

    for mapping in mappings:
        if selected and mapping.marker.upper() not in selected:
            continue
        snippet_path = root_path / mapping.snippet
        target_path = root_path / mapping.target
        if not snippet_path.exists():
            raise SnippetSyncError(
                build_error_payload(
                    code="snippets.missing_source",
                    message=f"Snippet '{snippet_path}' does not exist.",
                )
            )
        if not target_path.exists():
            raise SnippetSyncError(
                build_error_payload(
                    code="snippets.missing_target",
                    message=f"Target '{target_path}' does not exist.",
                )
            )
        options = SurgeonOptions(
            file=target_path,
            marker=mapping.marker,
            content_path=snippet_path,
            heading=mapping.heading,
            mode=mapping.mode,
        )
        synchronize_snippet(options)
        touched.append(target_path)
    return touched
