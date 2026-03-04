"""MCP test server with tools whose inputSchema fields lack description fields."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


async def health(request):
    return JSONResponse({"status": "ok"})


async def list_tools_endpoint(request):
    """Handle plain JSON-RPC tools/list requests for testing."""
    try:
        body = await request.json()
        if body.get("method") == "tools/list":
            # Return tools where inputSchema properties are missing description fields
            tools = [
                {
                    "name": "process_data",
                    "description": "Process the given data.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string"
                                # No "description" field intentionally omitted
                            },
                            "mode": {
                                "type": "string"
                                # No "description" field intentionally omitted
                            }
                        },
                        "required": ["data"]
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


app = Starlette(routes=[
    Route('/health', health, methods=['GET']),
    Route('/mcp', list_tools_endpoint, methods=['POST']),
])
