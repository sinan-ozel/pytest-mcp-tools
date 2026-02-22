FROM python:3.11-slim

WORKDIR /app

# Copy pyproject.toml and source code
COPY pyproject.toml .
COPY src/pytest_mcp_tools ./pytest_mcp_tools

# Install the plugin and dependencies
RUN pip install --upgrade pip
RUN pip install .
RUN pip install .[test]

# Copy sample tests for integration testing
COPY tests/test_samples /app/test_samples/

# Default command: run pytest with mcp-tools
CMD ["pytest", "--mcp-tools=http://test-server:8000", "-v"]
