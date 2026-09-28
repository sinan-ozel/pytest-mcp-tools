![Ci/CD Pipeline](https://github.com/sinan-ozel/pytest-mcp-tools/actions/workflows/ci.yaml/badge.svg?branch=main)
![PyPI](https://img.shields.io/pypi/v/pytest-mcp-tools.svg)
![Downloads](https://static.pepy.tech/badge/pytest-mcp-tools)
![Monthly Downloads](https://static.pepy.tech/badge/pytest-mcp-tools/month)
![License](https://img.shields.io/github/license/sinan-ozel/pypi-publish-with-cicd.svg)
[![Documentation](https://img.shields.io/badge/docs-github--pages-blue)](https://sinan-ozel.github.io/pytest-mcp-tools/)

# ✨ Introduction

🤖 **Your MCP server is only as good as what it tells the LLM.**

`pytest-mcp-tools` tests your MCP servers live — checking that schemas are correct,
examples actually work and match the schema, and that invalid input is rejected
the way the MCP spec expects.
The guiding principle is: good documentation reveals what the user needs to know,
whether the user is a human or an LLM or an agent.

This is meant to be run in a staging environment, right before an MCP server is deployed.
It can also run in production with `--mcp-tools-production` (alias `--mcp-tools-read-only`),
which restricts live tool calls to tools annotated `readOnlyHint: true`. It does not
support authentication currently.

```
pytest --mcp-tools=http://localhost:8000
```


```

🔍 MCP Tools: Discovering endpoints at http://docker-image:8000...
   Checking http://docker-image:8000...
   ✓ Server reachable (status: 404)
   ✓ Found endpoint: /mcp (status: 200)
   ✗ Endpoint /sse not found (status: 404)
   ✗ Endpoint /messages not found (status: 404)
✅ MCP Tools: Discovered endpoints: /mcp

============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2, pluggy-1.6.0 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /app
configfile: pyproject.toml
plugins: mcp-tools-0.2.1, anyio-4.12.1
collecting ... collected 0 items

created 14 tests
✅ MCP tools test created for discovered endpoints: /mcp

..::test_mcp_tools[POST /mcp] PASSED                                     [  7%]
..::test_list_tools_from_basic_server PASSED                             [ 14%]
..::test_tools_have_descriptions PASSED                                  [ 21%]
..::test_tools_have_names PASSED                                         [ 28%]
..::test_tools_have_unique_names PASSED                                  [ 35%]
..::test_invalid_request PASSED                                          [ 42%]
..::test_generate_spell_card_stream_input_schema_field_descriptions PASSED [ 50%]
..::test_generate_spell_card_stream_input_schema_field_types PASSED      [ 57%]
..::test_generate_spell_card_stream_example_0 PASSED                     [ 64%]
..::test_generate_spell_card_stream_example_1 PASSED                     [ 71%]
..::test_generate_spell_card_stream_schema_0 PASSED                      [ 78%]
..::test_generate_spell_card_stream_schema_1 PASSED                      [ 85%]
..::test_generate_spell_card_stream_missing_prompt PASSED                [ 92%]
..::test_generate_spell_card_stream_wrong_type_prompt PASSED             [100%]

============================== 14 passed in 0.62s ===============================
```

The exact set of generated tests depends on what your server's tools declare
(`inputSchema`, `outputSchema`, `annotations`). See the
[full docs](https://sinan-ozel.github.io/pytest-mcp-tools/) for every test the
plugin can generate and when.

# Reporting Issues
If you tested this on your server, and think that there is an issue,
just give me the docker image of your server in the issue,
and tell me what you are expecting, what you got.
If I can run your image locally, I will be able to test it,
and make it work for your use case.

If you don't have a docker hub image, give me a minimal example.
I will add a mock server with your minimal example to the testing harness.

## Typical Concerns

(I am just writing this down from personal experience working on MCP servers.)

* If the tests fail because this is is sending fields with `null` values, simply use Pydantic BaseModels with explicit format to explain that they are not allowed `null`. The checker validates, as per the MCP standard.
* If invalid-input tests fail with a `-32602` JSON-RPC error instead of a tool
  execution error, that's expected for servers built before the MCP
  2025-11-25 spec revision — add `--mcp-tools-legacy-invalid-params` to accept
  the older behavior, or update the server to return `isError: true` instead.


# Features

## Automated Tests

The plugin auto-generates tests to verify, among other things:
- At least one transport (`/mcp`, HTTP) is available
- Tools can be listed, and all have unique names, descriptions, and (when
  annotated) titles and consistent hints
- `inputSchema` fields all have descriptions and valid types
- Declared examples are valid against the schema and actually work when called
- Valid inputs derived directly from the schema succeed, and responses match
  `outputSchema` when declared
- Invalid input (missing required fields, wrong types) is rejected as the MCP
  spec requires — either a tool execution error (`isError: true`, current spec)
  or `-32602` (pre-2025-11-25 spec, via `--mcp-tools-legacy-invalid-params`)
- Malformed requests and unknown methods get the correct JSON-RPC protocol
  errors (`-32600`/`-32602`, `-32601`)
- `--mcp-tools-strict` — every tool has both examples and an `outputSchema`

See the [docs](https://sinan-ozel.github.io/pytest-mcp-tools/) for the complete,
up-to-date table of generated tests and CLI flags.

# Future Work

- Generate tool calls from field *descriptions* (not just schema types/examples),
  and from valid field *combinations* (some fields only make sense together).
- LLM-as-a-judge checks: are tool and field descriptions actually meaningful
  to a model, not just present?
- Run as a container with LLM-as-a-judge wired in, so no local Python/pytest
  setup is needed.
- Authorization support — I need to study what's used commonly first. Open an
  issue if you have a request.


# 🛠️ Development

The only requirement is 🐳 Docker.
(The `.devcontainer` and `tasks.json` are prepared assuming a *nix system, but if you know the commands, this will work on Windows, too.)

1. Clone the repo.
2. Branch out.
3. Open in "devcontainer" on VS Code and start developing. Run `pytest` under `tests` to test.
4. Alternatively, if you are a fan of Test-Driven Development like me, you can run the tests without getting on a container. `.vscode/tasks.json` has the command to do so, but it's also listed here:
```
docker compose -f tests/docker-compose.yaml --project-directory tests up --build --abort-on-container-exit --exit-code-from test
```
