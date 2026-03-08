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
- The `/mcp` HTTP endpoint
- Available tools and their metadata

## How It Works

The plugin automatically:

1. **Discovers the `/mcp` endpoint** by sending an HTTP request and checking the response

2. **Creates test cases** for:
   - HTTP endpoint presence
   - Tool listing functionality
   - Tool description validation
   - Tool name presence and uniqueness validation
   - Tool annotation validation (title presence and hint consistency)
   - Per-tool `inputSchema` field validation

3. **Runs tests** alongside your regular pytest tests

## Transport Support

### HTTP Streaming (`/mcp`)

The plugin tests the `/mcp` endpoint using JSON-RPC over HTTP POST — the current MCP standard.

```bash
pytest --mcp-tools=http://my-server:8000
```

### Deprecated Endpoints

- **GET /sse**: Server-Sent Events — **deprecated**, no longer a valid transport
- **GET /messages**: Messages endpoint — **deprecated**, no longer a valid transport

If `/sse` or `/messages` are detected, the plugin prints a deprecation warning
but does **not** count them as valid transports. No tests are generated for them.
Migrate to `/mcp` (HTTP streaming).

## Example Output

Server with 1 tool (5 generated tests):

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

When the server is not reachable or has no `/mcp` endpoint:

```
🔍 MCP Tools: Discovering endpoints at http://empty-server:8000...
   Checking http://empty-server:8000...
   ✓ Server reachable (status: 404)
   ✗ Endpoint /mcp not found (status: 404)
❌ MCP Tools: No MCP endpoints discovered!

============================= test session starts ==============================
.::test_mcp_tools[NO ENDPOINT FOUND] FAILED                             [100%]
```

## Features

### Test Generation

Automatically creates tests for every server with a `/mcp` endpoint:

| Test | Always? | Condition |
|---|---|---|
| `test_mcp_tools[POST /mcp]` | ✅ | HTTP endpoint found |
| `test_list_tools_from_basic_server` | ✅ | HTTP endpoint found |
| `test_tools_have_descriptions` | ✅ | HTTP endpoint found |
| `test_tools_have_names` | ✅ | HTTP endpoint found |
| `test_tools_have_unique_names` | ✅ | HTTP endpoint found |
| `test_tools_have_titles` | — | At least one tool has `annotations` |
| `test_tool_annotations_are_consistent` | — | At least one tool has `annotations` |
| `test_{tool}_input_schema_field_descriptions` | — | Per tool: tool has `inputSchema.properties` |
| `test_{tool}_input_schema_field_types` | — | Per tool: tool has `inputSchema.properties` |
| `test_{tool}_example_{n}` | — | Per tool per example: tool has `inputSchema.examples` (filtered by `readOnlyHint` when `--mcp-tools-production` or `--mcp-tools-read-only` is set) |
| `test_{tool}_schema_{n}` | — | Per tool: tool has `inputSchema.properties`; auto-generated from field types (marked `mcp_tools_schema`) |
| `test_{tool}_has_examples` | — | Per tool: `--mcp-tools-strict` set; fails if tool has no `inputSchema.examples` |
| `test_{tool}_has_output_schema` | — | Per tool: `--mcp-tools-strict` set; fails if tool has no `outputSchema` |

### Example-Based Live Call Tests

For every tool that declares an `inputSchema.examples` list, the plugin generates one test
per example (marked `mcp_tools_examples`):

```bash
# Run example tests for all tools
pytest --mcp-tools=http://localhost:8000

# Run example tests only for read-only tools (safe for production/staging)
pytest --mcp-tools=http://localhost:8000 --mcp-tools-production
pytest --mcp-tools=http://localhost:8000 --mcp-tools-read-only
```

Each generated test (named `test_{tool_name}_example_{n}`) does the following:

1. **Validates the example input** against the tool's `inputSchema` before
   making any network call:
   - All fields listed in `inputSchema.required` must be present in the example.
   - Each provided field value must match the declared JSON Schema `type`
     (`string`, `integer`, `number`, `boolean`, `array`, `object`, `null`).
   - Each string field with a `format` keyword (`email`, `uri`, `date`,
     `date-time`, `time`) must match the expected pattern.
   - The test fails immediately with a descriptive message if any violation is
     found, without ever calling the server.
2. Calls the tool via `tools/call` using the example as arguments.
3. Asserts the response contains no JSON-RPC error.
4. If the tool declares an `outputSchema`, validates that every field in
   `structuredContent` matches the declared JSON Schema type.

**`--mcp-tools-production` / `--mcp-tools-read-only`** (aliases, default `false`)

When either flag is set, example tests are only generated for tools where
`annotations.readOnlyHint` is `true`. This is useful for running safe smoke
tests against a live production or staging environment without triggering
side effects from write operations.

Example tool definition with examples and outputSchema:

```json
{
  "name": "get_greeting",
  "annotations": { "readOnlyHint": true },
  "inputSchema": {
    "type": "object",
    "properties": {
      "name": { "type": "string", "description": "The name to greet" }
    },
    "required": ["name"],
    "examples": [
      { "name": "World" },
      { "name": "Claude" }
    ]
  },
  "outputSchema": {
    "type": "object",
    "properties": {
      "greeting": { "type": "string", "description": "The greeting message" }
    }
  }
}
```

This would generate `test_get_greeting_example_0` and
`test_get_greeting_example_1`, each calling the tool and verifying the
`greeting` field in `structuredContent` is a string.

### Schema-Driven Live Call Tests

For every tool that declares `inputSchema.properties`, the plugin automatically
generates a set of valid inputs derived from the schema (marked
`mcp_tools_schema`) and calls the tool with each one, verifying the response
against `outputSchema`.

Tests are named `test_{tool_name}_schema_{n}` (0-based index).  The first case
(`schema_0`) uses the simplest valid value for every required field ("basic");
subsequent cases vary one field at a time while holding others at their basic
value.

Values generated per field type:

| Field type / format | Values generated |
|---|---|
| `string` (no format) | `"hello"`, UTF-8 Chinese, UTF-8 Turkish, emoji, single-quote, double-quote, SQL injection, HTML injection |
| `string` format `email` | 3 well-formed email addresses |
| `string` format `uri` | 3 well-formed URIs (`https://`, `http://`, `ftp://`) |
| `string` format `date` | 3 well-formed dates (`YYYY-MM-DD`) |
| `string` format `date-time` | 3 well-formed datetime strings |
| `string` format `time` | 3 well-formed time strings |
| `string` with `enum` | Every declared enum value |
| `number` (unconstrained) | `0`, `1`, `-1`, `1e15`, `-1e15`, `3.14` |
| `integer` (unconstrained) | `0`, `1`, `-1`, `10**15`, `-10**15`, `42` |
| `number` / `integer` with `minimum` / `maximum` | `minimum`, `maximum`, midpoint, zero (when in range) |
| `boolean` | `true`, `false` |

### Strict Mode

`--mcp-tools-strict` (default `false`) generates two compliance tests per tool:

- **`test_{tool_name}_has_examples`** — passes if the tool declares at least one
  entry in its `inputSchema.examples` list; fails otherwise.
- **`test_{tool_name}_has_output_schema`** — passes if the tool declares an
  `outputSchema` object; fails otherwise.

```bash
pytest --mcp-tools=http://localhost:8000 --mcp-tools-strict
```

Use this flag to enforce that every tool in your server is fully documented
with call examples and a structured output schema.

### inputSchema Field Validation

For every tool that declares `inputSchema.properties`, the plugin generates two
named tests (marked `mcp_tools_input_schema`):

- **`test_{tool_name}_input_schema_field_descriptions`**: every property at
  every nesting depth must carry a non-empty `description` string.

- **`test_{tool_name}_input_schema_field_types`**: every property at every
  nesting depth must have a `type` field set to one of the valid JSON Schema
  primitive types: `string`, `number`, `integer`, `boolean`, `array`,
  `object`, `null`.

Both checks recurse into nested `properties` objects, so a missing field deep
inside a three-level schema will still be caught.

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

### ✅ HTTP Servers

Servers exposing a `/mcp` endpoint (JSON-RPC over HTTP POST). This is the
current MCP standard and the only transport supported by this plugin.

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
