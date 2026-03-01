"""MCP test server with tools that have duplicate name fields."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


# Simple health check endpoint
async def health(request):
    return JSONResponse({"status": "ok"})


# JSON-RPC endpoint for listing tools (with duplicate names)
async def list_tools_endpoint(request):
    """Handle plain JSON-RPC tools/list requests for testing."""
    try:
        body = await request.json()
        if body.get("method") == "tools/list":
            # Return tools WITH duplicate name fields
            tools = [
                {
                    "name": "duplicate_tool",
                    "description": "First tool with a duplicate name.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Some input"
                            }
                        },
                        "required": ["input"]
                    }
                },
                {
                    "name": "duplicate_tool",
                    "description": "Second tool with the same duplicate name.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "Some input"
                            }
                        },
                        "required": ["input"]
                    }
                }
            ]
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id", 1),
                "result": {"tools": tools}
            })
    except Exception:
        pass

    return JSONResponse(
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
        status_code=400
    )


# Create Starlette app with routes
app = Starlette(routes=[
    Route('/health', health, methods=['GET']),
    Route('/mcp', list_tools_endpoint, methods=['POST']),
])
