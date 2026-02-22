"""Basic MCP test server with streaming tool."""

import os
import threading
import time
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Create FastMCP server
mcp = FastMCP(
    "Basic Test Server",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )
)

@mcp.tool()
async def stream_message(message: str) -> str:
    """Stream a given message back to the client.

    Args:
        message: The message to stream back

    Returns:
        The same message that was provided
    """
    return message


@mcp.custom_route("/health", methods=["GET"], name="health")
def _health(request):
    return JSONResponse({"status": "ok"})
