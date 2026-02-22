# Integration Testing

This directory contains integration tests for pytest-mcp-tools against live MCP servers.

## Usage

Run integration tests against the default server:
```bash
docker compose -f integration/docker-compose.yaml up --build --abort-on-container-exit
```

Run integration tests against a specific server:
```bash
TEST_SERVER_NAME=basic_server docker compose -f integration/docker-compose.yaml up --build --abort-on-container-exit
```

## Structure

- `docker-compose.yaml`: Orchestrates test server and pytest runner
- `Dockerfile`: Builds pytest runner container with pytest-mcp-tools installed
- Test files are loaded from `tests/test_samples/`

## How it works

1. The `test-server` container starts the selected MCP server
2. The `pytest-runner` container waits for the server to be healthy
3. Pytest runs with `--mcp-tools=http://test-server:8000` flag
4. Test results are displayed in the output
