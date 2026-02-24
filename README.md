![Ci/CD Pipeline](https://github.com/sinan-ozel/pytest-mcp-tools/actions/workflows/ci.yaml/badge.svg?branch=main)
![PyPI](https://img.shields.io/pypi/v/pytest-mcp-tools.svg)
![Downloads](https://static.pepy.tech/badge/pytest-mcp-tools)
![Monthly Downloads](https://static.pepy.tech/badge/pytest-mcp-tools/month)
![License](https://img.shields.io/github/license/sinan-ozel/pypi-publish-with-cicd.svg)
[![Documentation](https://img.shields.io/badge/docs-github--pages-blue)](https://sinan-ozel.github.io/pytest-mcp-tools/)

# ✨ Introduction

This is an opinionated tool for testing MCP servers live.
Currently, you point it at a live HTTP Streaming MCP server, and it checks if it can list the tools and whether they have descriptions.

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
plugins: anyio-4.12.1, mcp-tools-0.1.1

collecting ... collected 0 items
created 3 tests
✅ MCP tools test created for discovered endpoints: /mcp
   📡 HTTP streaming support detected

..::test_mcp_tools[POST /mcp] PASSED                                     [ 33%]
..::test_list_tools_from_basic_server PASSED                             [ 66%]
..::test_tools_have_descriptions PASSED                                  [100%]

============================== 3 passed in 0.02s ===============================
test-runner-for-docker-image exited with code 0
```

Later, it will have support for STDIO MCP servers, a check for limiting token count,
and calls for tools to see if they work as described.
I may also add LLM-as-a-Judge checks to see if the descriptions make sense,
or to generate reasonable calls.


# Reporting Issues
If you tested this on your server, and think that there is an issue, just give me the docker image of your server in the issue, and tell me what you are expecting, what you got.

If you don't have a docker hub image, give me a minimal example. That's all I need.

# 🛠️ Development

The only requirement is 🐳 Docker.
(The `.devcontainer` and `tasks.json` are prepared assuming a *nix system, but if you know the commands, this will work on Windows, too.)

1. Clone the repo.
2. Branch out.
3. Open in "devcontainer" on VS Code and start developing. Run `pytest` under `tests` to test.
4. Akternatively, if you are a fan of Test-Driven Development like me, you can run the tests without getting on a container. `.vscode/tasks.json` has the command to do so, but it's also listed here:
```
docker compose -f tests/docker-compose.yaml up --build --abort-on-container-exit --exit-code-from test
```
