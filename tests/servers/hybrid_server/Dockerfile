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

# Hybrid server - supports both HTTP and STDIO
# Default to STDIO mode (for docker run -i testing)
# docker-compose overrides this to run in HTTP mode for health checks
ENV MCP_ALLOW_HTTP=1
ENV MCP_TRUSTED_HOSTS=test-server:8000,127.0.0.1:8000,localhost:8000

# Default to STDIO mode - docker-compose will override for HTTP
CMD ["python", "-u", "server.py"]
