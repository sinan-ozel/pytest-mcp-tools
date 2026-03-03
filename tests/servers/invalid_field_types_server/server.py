"""MCP test server with tools whose inputSchema fields have missing or invalid type fields."""

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
            # Return a tool where inputSchema properties have missing or invalid type fields
            tools = [
                {
                    "name": "transform_data",
                    "description": "Transform the given data.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input_text": {
                                "type": "text",  # Invalid: "text" is not a valid JSON Schema type
                                "description": "The text to transform"
                            },
                            "count": {
                                # No "type" field intentionally omitted
                                "description": "How many times to transform"
                            }
                        },
                        "required": ["input_text"]
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
