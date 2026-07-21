# Read-only MCP server

The project includes a stdio-only adapter using the official `mcp` Python SDK.

```bash
uv run python -m mcp_server.server
```

It exposes compact semantic resources and six registry-checked read-only analytics tools. Default deny applies: only low-risk, read-only tools explicitly marked `mcp_exposable` can run. Paths, code, SQL, shell arguments, write operations, and raw files are rejected. Output is row capped and JSON sanitized.

No HTTP transport, remote authentication, OAuth, public deployment, or MCP UI is included.

Example client configuration:

```json
{"mcpServers":{"revenue-inventory-analytics":{"command":"uv","args":["--directory","/path/to/revenue-poc","run","python","-m","mcp_server.server"]}}}
```
