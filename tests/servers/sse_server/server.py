"""SSE-based MCP test server for testing deprecation warnings."""

from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# Create FastMCP server with SSE transport
mcp = FastMCP(
    "SSE Test Server",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    )
)

@mcp.tool()
async def example_tool(text: str) -> str:
    """An example tool for testing.

    Args:
        text: Input text

    Returns:
        The same text
    """
    return text


@mcp.custom_route("/health", methods=["GET"], name="health")
def _health(request):
    return JSONResponse({"status": "ok"})
