# SSE Server

This is a test MCP server that uses the deprecated HTTP/SSE transport.

It's used to test that pytest-mcp-tools correctly detects and warns about SSE-based endpoints.

## Expected Behavior

When pytest-mcp-tools discovers this server's `/mcp` endpoint, it should:
1. Receive a 406 Not Acceptable response (because we're not using SSE headers)
2. Recognize this as a deprecated SSE endpoint
3. Display a deprecation warning
4. Report that no valid endpoints were found (since SSE is not supported)
