FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN apt-get update \
	&& apt-get install -y --no-install-recommends curl \
	&& rm -rf /var/lib/apt/lists/* \
	&& pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server.py .

# Disable MCP SSE transport host validation for Docker networking
ENV MCP_ALLOW_HTTP=1
ENV MCP_TRUSTED_HOSTS=test-server:8000,127.0.0.1:8000,localhost:8000

# Set the entrypoint to run the server with uvicorn
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
