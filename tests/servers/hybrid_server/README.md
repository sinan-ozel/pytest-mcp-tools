# Hybrid MCP Test Server

This MCP server supports both HTTP and STDIO transports, demonstrating that a server can be dual-mode.

## Purpose

This server is used for testing the pytest-mcp-tools plugin's ability to detect servers that support both HTTP and STDIO transports.

## Modes

### HTTP Mode (default)
- Exposes port 8000
- Endpoints: `/health` (GET), `/mcp` (POST)
- Runs with: `uvicorn server:app --host 0.0.0.0 --port 8000`

### STDIO Mode
- No ports exposed
- Communicates via stdin/stdout
- Runs with: `python server.py` (with MCP_MODE=stdio)

## Tools

- `hybrid_tool`: A tool that works via both HTTP and STDIO

## Usage

### HTTP Mode
```bash
docker build -t hybrid-server .
docker run -p 8000:8000 hybrid-server
curl http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### STDIO Mode
```bash
docker build -t hybrid-server .
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | \
  docker run -i --entrypoint python hybrid-server server.py
```
