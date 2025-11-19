"""Behavioral tests for the stdio-based MCP server loop."""

from __future__ import annotations

import asyncio
import io
import json
from typing import Any

from sentinelkit.cli.mcp.server import _serve_async


def _decode_single_message(buffer: bytes) -> dict[str, Any]:
    """Parse a single Content-Length framed JSON-RPC message from a buffer."""

    text = buffer.decode("ascii", errors="replace")
    header, _, body = text.partition("\r\n\r\n")
    assert header.startswith("Content-Length:"), header
    payload = json.loads(body)
    assert isinstance(payload, dict)
    return payload


def test_stdio_server_sends_server_ready_notification(repo_root) -> None:
    """_serve_async should emit notifications/serverReady immediately on startup."""

    reader = io.BytesIO(b"")
    writer = io.BytesIO()

    asyncio.run(_serve_async(root=repo_root, reader=reader, writer=writer))

    payload = _decode_single_message(writer.getvalue())
    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "notifications/serverReady"
    params = payload["params"]
    assert params["protocolVersion"] == "2024-11-01"
    assert params["serverInfo"]["name"] == "sentinel-mcp"

