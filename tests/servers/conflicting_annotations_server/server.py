"""MCP test server with tools that have conflicting annotation hints."""

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
                    "name": "readonly_but_destructive",
                    "description": "A tool incorrectly marked as both read-only"
                    " and destructive.",
                    "annotations": {
                        "title": "Read-Only But Destructive",
                        "readOnlyHint": True,
                        "destructiveHint": True,
                    },
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to operate on"
                            }
                        },
                        "required": ["key"]
                    }
                },
                {
                    "name": "readonly_but_idempotent",
                    "description": "A tool incorrectly marked as both read-only"
                    " and idempotent.",
                    "annotations": {
                        "title": "Read-Only But Idempotent",
                        "readOnlyHint": True,
                        "idempotentHint": True,
                    },
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to operate on"
                            }
                        },
                        "required": ["key"]
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
