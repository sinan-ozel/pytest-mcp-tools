"""MCP test server with a tool whose outputSchema fields are missing descriptions."""

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
            tools = [
                {
                    "name": "analyze_data",
                    "description": "Analyze the given data.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "data": {
                                "type": "string",
                                "description": "The data to analyze"
                            }
                        },
                        "required": ["data"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "result": {
                                "type": "string"
                                # No "description" intentionally omitted
                            },
                            "score": {
                                "type": "number"
                                # No "description" intentionally omitted
                            }
                        }
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
