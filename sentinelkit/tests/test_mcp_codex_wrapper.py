"""Tests for the Codex MCP stdout wrapper."""

from __future__ import annotations

import io
import json
from typing import Any, Mapping

from sentinelkit.cli.mcp import codex_wrapper


def _decode_single_message(buffer: bytes) -> Mapping[str, Any]:
    text = buffer.decode("ascii", errors="replace")
    header, _, body = text.partition("\r\n\r\n")
    assert header.startswith("Content-Length:"), header
    payload: Any = json.loads(body)
    assert isinstance(payload, dict)
    return payload


def test_wrapper_builds_server_ready_payload() -> None:
    payload = codex_wrapper._build_server_ready()
    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "notifications/serverReady"
    params = payload["params"]
    assert params["protocolVersion"] == "2024-11-01"
    assert params["serverInfo"]["name"] == "sentinel-mcp"


def test_wrapper_writes_framed_message(monkeypatch) -> None:
    buffer = io.BytesIO()

    class _Stream:
        def __init__(self, inner: io.BytesIO) -> None:
            self._inner = inner

        def write(self, data: bytes) -> None:
            self._inner.write(data)

        def flush(self) -> None:  # pragma: no cover - BytesIO flush is a no-op
            pass

    monkeypatch.setattr(codex_wrapper.sys, "stdout", type("S", (), {"buffer": _Stream(buffer)})())
    codex_wrapper._write_framed({"jsonrpc": "2.0", "method": "ping", "params": {}})

    payload = _decode_single_message(buffer.getvalue())
    assert payload["method"] == "ping"

