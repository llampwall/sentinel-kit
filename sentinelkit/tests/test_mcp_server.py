"""Tests for the asyncio MCP server dispatcher."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from sentinelkit.cli.mcp.server import SentinelMCPServer

FIXTURE_LEDGER = Path(__file__).parent / "fixtures" / "DECISIONS.sample.md"


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """Seed a minimal repo layout consumed by the MCP server."""
    sentinel_dir = tmp_path / ".sentinel"
    contracts_dir = sentinel_dir / "contracts"
    fixtures_dir = contracts_dir / "fixtures" / "sample.v1"
    tests_dir = tmp_path / "tests" / "sentinels"

    contracts_dir.mkdir(parents=True)
    fixtures_dir.mkdir(parents=True)
    tests_dir.mkdir(parents=True)

    (contracts_dir / "sample.v1.yaml").write_text(
        """
contract: sample.v1
schema:
  type: object
  required: ["metadata", "value"]
  properties:
    metadata:
      type: object
      required: ["ProducedBy"]
      properties:
        ProducedBy:
          type: string
    value:
      type: integer
""".strip(),
        encoding="utf-8",
    )

    (fixtures_dir / "ok.json").write_text(
        '{"metadata": {"ProducedBy": "TEST-AGENT"}, "value": 42}',
        encoding="utf-8",
    )

    (tests_dir / "test_sample.py").write_text(
        "def test_sample() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    (sentinel_dir / "DECISIONS.md").write_text(
        FIXTURE_LEDGER.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    return tmp_path


@pytest.fixture()
def server(repo_root: Path) -> SentinelMCPServer:
    return SentinelMCPServer(root=repo_root)


def _dispatch(server: SentinelMCPServer, payload: dict[str, Any]) -> dict[str, Any]:
    """Run the async handler synchronously for test convenience."""
    return asyncio.run(server.handle_message(payload))


def test_initialize_and_tools_list(server: SentinelMCPServer) -> None:
    init_response = _dispatch(server, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_response["result"]["protocolVersion"] == "2024-11-01"

    list_response = _dispatch(server, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    tools = list_response["result"]["tools"]
    tool_names = {tool["name"] for tool in tools}
    assert tool_names == {
        "mcp.sentinel.contract_validate",
        "mcp.sentinel.sentinel_run",
        "mcp.sentinel.decision_log",
    }


def test_contract_validate_tool(server: SentinelMCPServer) -> None:
    response = _dispatch(
        server,
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "mcp.sentinel.contract_validate",
                "arguments": {"contract": "sample.v1"},
            },
        },
    )
    payload = response["result"]["content"][0]["json"]
    assert payload["ok"] is True
    assert payload["results"][0]["contract"] == "sample.v1"


def test_sentinel_run_tool(server: SentinelMCPServer) -> None:
    response = _dispatch(
        server,
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "mcp.sentinel.sentinel_run", "arguments": {}},
        },
    )
    summary = response["result"]["content"][0]["json"]
    assert summary["ok"] is True
    assert summary["exit_code"] == 0


def test_decision_log_tool_dry_run(server: SentinelMCPServer, repo_root: Path) -> None:
    preview_path = Path("preview") / "decision.md"
    response = _dispatch(
        server,
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "mcp.sentinel.decision_log",
                "arguments": {
                    "author": "Builder",
                    "scope": ["docs/README.md", "src/app.py"],
                    "decision": "Add MCP server",
                    "rationale": "Spec requires Python parity",
                    "outputs": ["sentinelkit/cli/mcp/server.py"],
                    "dry_run": True,
                    "preview": str(preview_path),
                },
            },
        },
    )

    result = response["result"]["content"][0]["json"]
    assert result["dry_run"] is True
    preview_file = repo_root / preview_path
    assert Path(result["preview"]) == preview_file.resolve()
    assert preview_file.exists()


def test_unknown_tool_errors(server: SentinelMCPServer) -> None:
    response = _dispatch(
        server,
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "mcp.sentinel.unknown", "arguments": {}},
        },
    )
    assert response["error"]["code"] == -32601
