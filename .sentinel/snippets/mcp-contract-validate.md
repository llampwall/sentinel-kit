<!-- ProducedBy=BUILDER RulesHash=BUILDER@1.0 Decision=D-0014 -->
### MCP contract validator

Use the MCP server when you need JSON-RPC tooling access to the contract fixtures without leaving your editor.

**Commands**
- `pnpm --dir=.sentinel mcp:contract-validate` starts the stdio server (press `Ctrl+C` to stop).
- `pnpm --dir=.sentinel mcp:contract-validate:smoke` runs the initialize → tools/list → tools/call handshake.

### MCP sentinel + decision log servers

- `pnpm --dir=.sentinel mcp:sentinel-run` exposes the `sentinel_run` tool (accepts optional `filter`).
- `pnpm --dir=.sentinel mcp:sentinel-run:smoke` verifies the server before CI.
- `pnpm --dir=.sentinel mcp:decision-log` wraps the decision-log CLI for ledger append.
- `pnpm --dir=.sentinel mcp:decision-log:smoke` sanity-checks the append path.

**.mcp.json snippet**
```json
{
  "mcpServers": {
    "contract-validate": {
      "command": "pnpm",
      "args": ["--dir=.sentinel", "mcp:contract-validate"],
      "env": {
        "NODE_ENV": "production"
      }
    },
    "sentinel-run": {
      "command": "pnpm",
      "args": ["--dir=.sentinel", "mcp:sentinel-run"],
      "env": {
        "NODE_ENV": "production"
      }
    },
    "decision-log": {
      "command": "pnpm",
      "args": ["--dir=.sentinel", "mcp:decision-log"],
      "env": {
        "NODE_ENV": "production"
      }
    }
  }
}
```
- Add API keys or additional env vars per server inside `env` as needed.
- The servers watch `.sentinel/contracts/**` and `.sentinel/DECISIONS.md`, so you can keep them running while editing.
