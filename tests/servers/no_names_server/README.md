# No Names Server

This is a test MCP server for pytest-mcp-tools that returns tools missing the `name` field.

## Purpose

This server is used to test that the pytest-mcp-tools plugin correctly validates that all tools have a `name` field.

## What it does

- Exposes a `/mcp` endpoint that handles JSON-RPC `tools/list` requests
- Returns a tool object that is missing the `name` field
- Used to ensure the `test_tools_have_names` test fails appropriately

## Running

```bash
docker build -t no-names-server .
docker run -p 8000:8000 no-names-server
```
