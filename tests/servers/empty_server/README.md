# Empty MCP Server

This is a test server with no MCP tools defined.

## Purpose

This server is used for testing the pytest-mcp-tools plugin behavior when:
- An MCP server is running but has no tools
- All MCP endpoints should return 404 responses
- The test should properly fail when no tools are available

## Endpoints

None - this server intentionally has no tools defined.
