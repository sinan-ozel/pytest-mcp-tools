"""MCP test server with a three-level nested inputSchema where the innermost field lacks a description."""

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
                    "name": "nested_call",
                    "description": "Perform a nested call.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "request": {                      # level 1 - has description and type
                                "type": "object",
                                "description": "The request wrapper",
                                "properties": {
                                    "payload": {              # level 2 - has description and type
                                        "type": "object",
                                        "description": "The payload object",
                                        "properties": {
                                            "value": {        # level 3 - missing description
                                                "type": "string"
                                            }
                                        }
                                    }
                                }
                            }
                        },
                        "required": ["request"]
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
