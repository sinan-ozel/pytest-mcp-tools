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
- HTTP endpoints (`/mcp` — current; `/sse` and `/messages` — deprecated)
- STDIO transport support (if the container is accessible via Docker)
- Available tools and their metadata

## How It Works

The plugin automatically:

1. **Discovers MCP endpoints** by checking:
   - `/mcp` - HTTP streaming endpoint (POST) — current standard
   - `/sse` - Server-Sent Events endpoint (GET) — **deprecated**
   - `/messages` - Messages endpoint (GET) — **deprecated**

2. **Detects STDIO support** by attempting to communicate with the container via stdin/stdout

3. **Creates test cases** for:
   - Discovered HTTP endpoints
   - STDIO transport (if available)
   - Tool listing functionality
   - Tool description validation
   - Tool name presence and uniqueness validation
   - Tool annotation validation (title presence and hint consistency)

4. **Runs tests** alongside your regular pytest tests

## Transport Support

The plugin supports multiple MCP transport methods:

### HTTP Endpoints
- **POST /mcp**: HTTP streaming (JSON-RPC over HTTP) — the current standard
- **GET /sse**: Server-Sent Events — **deprecated**, no longer a valid transport
- **GET /messages**: Messages endpoint — **deprecated**, no longer a valid transport

If `/sse` or `/messages` are detected, the plugin prints a deprecation warning
and does **not** count them as valid transports. No tests are generated for them.
Migrate to `/mcp` (HTTP streaming) or STDIO.

### STDIO Transport

**Via Docker (HTTP URL):** When you pass an `http://` URL, the plugin
extracts the container name and attempts STDIO communication via `docker run -i`:

```bash
pytest --mcp-tools=http://my-server:8000
```

**Via subprocess (stdio:// URL):** For local or CI usage where the server
binary is on `PATH`, pass a `stdio://` URL:

```bash
pytest --mcp-tools=stdio://my-mcp-server-command
```

### Hybrid Servers
The plugin recognizes when a server supports both HTTP and STDIO:
- Tests both transports independently
- Validates tool listing works via both methods
- Reports which transports are available

## Example Output

HTTP-only server (5 generated tests):

```
🔍 MCP Tools: Discovering endpoints at http://my-server:8000...
   Checking http://my-server:8000...
   ✓ Server reachable (status: 404)
   ✓ Found endpoint: /mcp (status: 200)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
✅ MCP Tools: Discovered endpoints: /mcp

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0
plugins: mcp-tools-0.1.4
collecting ... collected 8 items

created 5 tests
✅ MCP tools test created for discovered endpoints: /mcp
   📡 HTTP streaming support detected

test_samples/test_sample_math.py::test_sample_addition PASSED            [ 12%]
test_samples/test_sample_math.py::test_sample_multiplication PASSED      [ 25%]
test_samples/test_sample_math.py::test_sample_string_operations PASSED   [ 37%]
.::test_mcp_tools[POST /mcp] PASSED                                      [ 50%]
.::test_list_tools_from_basic_server PASSED                              [ 62%]
.::test_tools_have_descriptions PASSED                                   [ 75%]
.::test_tools_have_names PASSED                                          [ 87%]
.::test_tools_have_unique_names PASSED                                   [100%]

============================== 8 passed in 0.05s ===============================
```

Server with annotations (2 extra tests generated):

```
.::test_tools_have_titles PASSED                                         [ 87%]
.::test_tool_annotations_are_consistent PASSED                           [100%]
```

When no MCP transport is found:

```
🔍 MCP Tools: Discovering endpoints at http://empty-server:8000...
   Checking http://empty-server:8000...
   ✓ Server reachable (status: 404)
   ✗ Endpoint /mcp not found (status: 404)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
❌ MCP Tools: No MCP endpoints discovered!
🔍 MCP Tools: Checking STDIO support for empty-server...
   ✗ STDIO not available: STDIO communication failed...

============================= test session starts ==============================
.::test_mcp_tools[NO TRANSPORT FOUND] FAILED                            [100%]

=========================== FAILURES ===========================
No MCP endpoints found at http://empty-server:8000.
Expected at least one of: /mcp, /sse, /messages
```

## Features

### Transport Detection
The plugin automatically detects:
- **HTTP endpoints**: /mcp, /sse, /messages
- **STDIO support**: Via `docker run -i` (container name from HTTP URL) or subprocess (`stdio://` URL)
- **Hybrid servers**: Supporting both transports

### Test Generation
Automatically creates tests for every HTTP server with endpoints:

| Test | Always? | Condition |
|---|---|---|
| `test_mcp_tools[POST /mcp]` | ✅ | HTTP endpoint found |
| `test_list_tools_from_basic_server` | ✅ | HTTP endpoint found |
| `test_tools_have_descriptions` | ✅ | HTTP endpoint found |
| `test_tools_have_names` | ✅ | HTTP endpoint found |
| `test_tools_have_unique_names` | ✅ | HTTP endpoint found |
| `test_list_tools_via_stdio` | — | STDIO also available |
| `test_tools_have_titles` | — | At least one tool has `annotations` |
| `test_tool_annotations_are_consistent` | — | At least one tool has `annotations` |

### Annotation Validation

When tools include an `annotations` field, the plugin validates:

- **`test_tools_have_titles`**: every annotated tool must have a non-empty
  `title` in its `annotations` object.

- **`test_tool_annotations_are_consistent`**: `readOnlyHint` must not be
  `true` at the same time as `destructiveHint` or `idempotentHint`, as
  those combinations are contradictory.

Example of a valid annotation:

```json
{
  "name": "delete_record",
  "annotations": {
    "title": "Delete Record",
    "readOnlyHint": false,
    "destructiveHint": true,
    "idempotentHint": false
  }
}
```

## Supported Server Types

The plugin fully supports all three types of MCP servers:

### ✅ HTTP-Only Servers
- Discovers endpoints via HTTP requests
- Tests tool listing, descriptions, names, uniqueness, and annotations
- Example: Servers exposing `/mcp` endpoint

### ✅ STDIO-Only Servers
- Spawns new container instances for testing via `docker run -i`
- Or communicates with a local process via `stdio://` URL
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
