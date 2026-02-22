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

## How It Works

The plugin automatically:

1. **Discovers MCP endpoints** by checking:
   - `/mcp` - HTTP streaming endpoint (POST)
   - `/sse` - Server-Sent Events endpoint (GET)
   - `/messages` - Messages endpoint (GET)

2. **Creates test cases** for discovered endpoints

3. **Runs tests** alongside your regular pytest tests

## Example Output

When endpoints are found:

```
🔍 MCP Tools: Discovering endpoints at http://test-server:8000...
   Retry 1/10: Checking http://test-server:8000...
   ✓ Server reachable (status: 404)
   ✓ Found endpoint: /mcp (status: 406)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
✅ MCP Tools: Discovered endpoints: /mcp

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0
plugins: mcp-tools-0.1.0
collecting ... collected 4 items

✅ MCP tools test created for discovered endpoints: /mcp
   📡 HTTP streaming support detected

test_samples/test_sample_math.py::test_sample_addition PASSED            [ 25%]
test_samples/test_sample_math.py::test_sample_multiplication PASSED      [ 50%]
.::test_mcp_tools[POST /mcp] PASSED                                      [ 75%]
test_samples/test_sample_math.py::test_sample_string_operations PASSED   [100%]

============================== 4 passed in 0.03s ===============================
```

When no endpoints are found:

```
🔍 MCP Tools: Discovering endpoints at http://empty-server:8000...
   Retry 1/10: Checking http://empty-server:8000...
   ✓ Server reachable (status: 404)
   ✗ Endpoint /mcp not found (status: 404)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
❌ MCP Tools: No endpoints discovered! Server is not a valid MCP server.

============================= test session starts ==============================
.::test_mcp_tools[NO ENDPOINTS FOUND] FAILED                            [100%]

=========================== FAILURES ===========================
No MCP endpoints found at http://empty-server:8000. 
Expected at least one of: /mcp, /sse, /messages
```

## Performance Optimization

The plugin optimizes endpoint discovery:

- **404 responses are not retried** - If an endpoint returns 404, it won't be checked again in subsequent retries
- **Early exit** - Discovery stops immediately when all endpoints return 404

This reduces wait time when testing servers with missing or incomplete MCP implementations.

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
