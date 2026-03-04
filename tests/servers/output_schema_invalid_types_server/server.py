"""MCP test server with a tool whose outputSchema fields have invalid or missing types."""

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
                    "name": "transform_result",
                    "description": "Transform and return a result.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "input": {
                                "type": "string",
                                "description": "The input to transform"
                            }
                        },
                        "required": ["input"]
                    },
                    "outputSchema": {
                        "type": "object",
                        "properties": {
                            "output": {
                                "type": "text",  # Invalid: "text" is not a valid JSON Schema type
                                "description": "The transformed output"
                            },
                            "count": {
                                # No "type" field intentionally omitted
                                "description": "The number of transformations applied"
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
