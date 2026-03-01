# pytest-mcp-tools

A pytest plugin for automatically testing MCP (Model Context Protocol) tool servers.

## Installation

```bash
pip install pytest-mcp-tools
```

## Quick Start

Run pytest with the `--mcp-tools` flag pointing to your MCP server:

```bash
pytest --mcp-tools=http://localhost:8000
```

The plugin will automatically detect:
- HTTP endpoints (/mcp, /sse, /messages)
- STDIO transport support (if the container is accessible)
- Available tools and their descriptions

## How It Works

The plugin automatically:

1. **Discovers MCP endpoints** by checking:
   - `/mcp` - HTTP streaming endpoint (POST)
   - `/sse` - Server-Sent Events endpoint (GET)
   - `/messages` - Messages endpoint (GET)

2. **Detects STDIO support** by attempting to communicate with the container via stdin/stdout

3. **Creates test cases** for:
   - Discovered HTTP endpoints
   - STDIO transport (if available)
   - Tool listing functionality
   - Tool description validation
   - Tool name uniqueness validation

4. **Runs tests** alongside your regular pytest tests

## Transport Support

The plugin supports multiple MCP transport methods:

### HTTP Endpoints
- **POST /mcp**: HTTP streaming (JSON-RPC over HTTP)
- **GET /sse**: Server-Sent Events (deprecated)
- **GET /messages**: Messages endpoint

### STDIO Transport
For containerized MCP servers, the plugin can detect and test STDIO communication:
- Automatically extracts the container name from the HTTP URL
- Spawns a new container instance using `docker run -i` for testing
- Communicates via stdin/stdout with proper JSON-RPC protocol
- Creates additional tests for STDIO functionality

### Hybrid Servers
The plugin recognizes when a server supports both HTTP and STDIO:
- Tests both transports independently
- Validates tool listing works via both methods
- Reports which transports are available

## Example Output

When endpoints are found:

```
🔍 MCP Tools: Discovering endpoints at http://test-server:8000...
   Checking http://test-server:8000...
   ✓ Server reachable (status: 404)
   ✓ Found endpoint: /mcp (status: 200)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
✅ MCP Tools: Discovered endpoints: /mcp
🔍 MCP Tools: Checking STDIO support for test-server...
   ✓ STDIO communication successful (1 tool(s) found)

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0
plugins: mcp-tools-0.1.2
collecting ... collected 5 items

created 4 tests
✅ MCP tools test created for discovered endpoints: /mcp
   📡 HTTP streaming support detected
   📡 STDIO transport support detected

test_samples/test_sample_math.py::test_sample_addition PASSED            [ 20%]
test_samples/test_sample_math.py::test_sample_multiplication PASSED      [ 40%]
.::test_mcp_tools[POST /mcp] PASSED                                      [ 60%]
.::test_list_tools_from_basic_server PASSED                              [ 80%]
.::test_list_tools_via_stdio PASSED                                      [100%]

============================== 5 passed in 0.03s ===============================
```

When no endpoints are found:

```
🔍 MCP Tools: Discovering endpoints at http://empty-server:8000...
   Checking http://empty-server:8000...
   ✓ Server reachable (status: 404)
   ✗ Endpoint /mcp not found (status: 404)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
❌ MCP Tools: No endpoints discovered! Server is not a valid MCP server.
🔍 MCP Tools: Checking STDIO support for empty-server...
   ✗ STDIO not available: STDIO communication failed...

============================= test session starts ==============================
.::test_mcp_tools[NO ENDPOINTS FOUND] FAILED                            [100%]

=========================== FAILURES ===========================
No MCP endpoints found at http://empty-server:8000.
Expected at least one of: /mcp, /sse, /messages
```

## Features

### Transport Detection
The plugin automatically detects:
- **HTTP endpoints**: /mcp, /sse, /messages
- **STDIO support**: Via docker exec communication
- **Hybrid servers**: Supporting both transports

### Test Generation
Automatically creates tests for:
- Endpoint discovery and availability
- Tool listing functionality (HTTP and/or STDIO)
- Tool description validation
- Tool name presence and uniqueness validation
- Per-transport functionality verification

## Supported Server Types

The plugin fully supports all three types of MCP servers:

### ✅ HTTP-Only Servers
- Discovers endpoints via HTTP requests
- Tests tool listing and descriptions
- Example: Servers exposing `/mcp` endpoint

### ✅ STDIO-Only Servers  
- Spawns new container instances for testing
- Uses `docker run -i` to communicate via stdin/stdout
- Example: `mcp/paper-search` and similar STDIO-first servers

### ✅ Hybrid Servers
- Detects and tests both HTTP and STDIO transports
- Creates separate tests for each transport
- Validates both communication methods work correctly

## Integration with Regular Tests

The plugin works seamlessly with your existing pytest tests. MCP tools tests run alongside your regular test suite without interference.

## Reporting Issues

If you encounter issues:

1. Provide your server's Docker image
2. Describe what you expected vs. what you got

If you don't have a Docker Hub image, provide a minimal reproducible example.

## Development

Development requires only 🐳 Docker.

1. Clone the repository
2. Create a branch
3. Open in VS Code devcontainer
4. Run tests:
   ```bash
   docker compose -f tests/docker-compose.yaml up --build --abort-on-container-exit --exit-code-from test
   ```

## License

See [LICENSE](https://github.com/<ORGANIZATION>/<MODULE-NAME>/blob/main/LICENSE) file.
