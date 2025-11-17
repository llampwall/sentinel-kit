<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0014 -->
### MCP contract validator

Use the Python MCP server when you need JSON-RPC tooling access to contracts, sentinel tests, or the decision ledger without leaving your editor.

**Commands**
- `uvx sentinel mcp server` starts the stdio JSON-RPC server (press `Ctrl+C` to stop). It serves `mcp.sentinel.contract_validate`, `mcp.sentinel.sentinel_run`, and `mcp.sentinel.decision_log`.
- `uvx sentinel mcp smoke` runs the initialize → tools/list → tools/call handshake against the Python server (use `--timeout-call 60` when your sentinel suites take longer).

**.mcp.json snippet**
```json
{
  "mcpServers": {
    "sentinel": {
      "command": "uvx",
      "args": ["sentinel", "mcp", "server"],
      "env": {
        "PYTHONUTF8": "1"
      }
    }
  }
}
```
- Add API keys or additional env vars inside `env` as needed (e.g., `SENTINEL_DECISION_AGENT` overrides ProducedBy defaults).
- The server watches `.sentinel/contracts/**`, `tests/sentinels/**`, and `.sentinel/DECISIONS.md`, so you can keep it running while editing.
