"""Stdout wrapper to make Sentinel's MCP server Codex-friendly.

Some MCP clients (including certain Codex harness modes) wait for the server to
write *something* to stdout before sending the initial ``initialize`` request.
The core Sentinel MCP server is intentionally passive and only responds after
``initialize``, which can lead to a startup deadlock.

This wrapper prints a single ``notifications/serverReady`` JSON-RPC notification
to stdout using the same framing as the real server, then ``exec``'s the
canonical ``sentinelkit.cli.mcp.server`` module so that the subsequent MCP
handshake is fully spec-compliant.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Mapping

from sentinelkit import get_version

JSONRPC_VERSION = "2.0"
PROTOCOL_VERSION = "2024-11-01"
SERVER_NAME = "sentinel-mcp"


def _build_server_ready() -> Mapping[str, Any]:
    return {
        "jsonrpc": JSONRPC_VERSION,
        "method": "notifications/serverReady",
        "params": {
            "protocolVersion": PROTOCOL_VERSION,
            "serverInfo": {
                "name": SERVER_NAME,
                "version": get_version(),
            },
        },
    }


def _write_framed(payload: Mapping[str, Any]) -> None:
    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
    stream = sys.stdout.buffer
    stream.write(header)
    stream.write(encoded)
    stream.flush()


def main() -> None:
    """Emit a readiness notification, then replace this process with the server."""

    _write_framed(_build_server_ready())
    os.execv(sys.executable, [sys.executable, "-m", "sentinelkit.cli.mcp.server"])


if __name__ == "__main__":  # pragma: no cover
    main()

