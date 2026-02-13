# MCP Servers

Add individual MCP server configuration modules here.

Each server should be registered in `../config.json` for auto-loading.

## Adding a New MCP Server

1. Add the server configuration to `engine/mcp/config.json`
2. Set `"enabled": true` to activate it
3. Environment variables can be referenced as `"${VAR_NAME}"`
4. The MCPManager resolves env vars at runtime
