![Ci/CD Pipeline](https://github.com/sinan-ozel/pytest-mcp-tools/actions/workflows/ci.yaml/badge.svg?branch=main)
![PyPI](https://img.shields.io/pypi/v/pytest-mcp-tools.svg)
![Downloads](https://static.pepy.tech/badge/pytest-mcp-tools)
![Monthly Downloads](https://static.pepy.tech/badge/pytest-mcp-tools/month)
![License](https://img.shields.io/github/license/sinan-ozel/pypi-publish-with-cicd.svg)
[![Documentation](https://img.shields.io/badge/docs-github--pages-blue)](https://sinan-ozel.github.io/pytest-mcp-tools/)

# ✨ Introduction

🤖 **Your MCP server is only as good as what it tells the LLM.**

`pytest-mcp-tools` tests your MCP servers live — checking that schemas are correct,
examples actually work and match the schema,
and incorrect inputs generate errors.
The guiding principle is: good documentation reveals what the user needs to know,
whether the user is a human or an LLM or an agent.

This is meant to be run in a staging environment, right before an MCP server is deployed.
It can also run in production with the `--mcp-tools-production=true` set, it will then
call only the tools annotated as read-only. However, it does not support
authentication currently.

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
plugins: mcp-tools-0.1.8, anyio-4.12.1
collecting ... collected 0 items

created 5 tests
✅ MCP tools test created for discovered endpoints: /mcp
docker-image-1  | INFO:     172.28.0.3:39934 - "POST /mcp HTTP/1.1" 200 OK



..::test_mcp_tools[POST /mcp] PASSED                                     [ 11%]
..::test_list_tools_from_basic_server PASSED                             [ 22%]
..::test_tools_have_descriptions PASSED                                  [ 33%]
..::test_tools_have_names PASSED                                         [ 44%]
..::test_tools_have_unique_names PASSED                                  [ 55%]
..::test_generate_spell_card_stream_input_schema_field_descriptions PASSED [ 66%]
..::test_generate_spell_card_stream_input_schema_field_types PASSED      [ 77%]
..::test_generate_spell_card_stream_example_0 PASSED                     [ 88%]
..::test_generate_spell_card_stream_example_1 PASSED                     [100%]

============================== 9 passed in 0.50s ===============================
```

# Reporting Issues
If you tested this on your server, and think that there is an issue,
just give me the docker image of your server in the issue,
and tell me what you are expecting, what you got.
If I can run your image locally, I will be able to test it,
and make it work for your use case.

If you don't have a docker hub image, give me a minimal example.
I will add a mock server with your minimal example to the testing harness.


# Future Work

I have two plans:
1. Run it as a container. In this mode, it will also use LLM-as-a-judge for additional tests, to make sure that descriptions and error messages make sense.
2. I want to add authotization, but I need study what is used commonly, first. Add an issue if you have a request.

# Features

## Automated Tests
The plugin generates tests to verify:
- At least one transport is available (HTTP or STDIO)
- Tools can be listed successfully
- All tools have description fields

Later versions will include:
- Call the tools, based on annotations.
- Check the responses from the tools against `outputSchema`
- Token count limiting checks
- LLM-as-a-Judge checks to validate description quality
- oAuth and perhaps CORS, as needed. (This is not strictly necessary, because I am imagining that this is going run as a staging test in an environment where all servers are trusted.)


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
