"""Empty test server with no MCP endpoints.

This server has no MCP endpoints and should return 404
for the MCP endpoint request (/mcp).
It only has a /health endpoint for Docker health checks.
"""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health(request):
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})


# Create a basic Starlette app with only health endpoint
# No MCP endpoints are defined
app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
    ]
)
