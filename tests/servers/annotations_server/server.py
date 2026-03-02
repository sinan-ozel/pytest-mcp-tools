"""MCP test server with tools that have proper annotations."""

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
                    "name": "read_data",
                    "description": "Read data from the data store.",
                    "annotations": {
                        "title": "Read Data",
                        "readOnlyHint": True,
                        "idempotentHint": False,
                        "destructiveHint": False,
                    },
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to read"
                            }
                        },
                        "required": ["key"]
                    }
                },
                {
                    "name": "write_data",
                    "description": "Write data to the data store.",
                    "annotations": {
                        "title": "Write Data",
                        "readOnlyHint": False,
                        "idempotentHint": True,
                        "destructiveHint": False,
                    },
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to write"
                            },
                            "value": {
                                "type": "string",
                                "description": "The value to write"
                            }
                        },
                        "required": ["key", "value"]
                    }
                },
                {
                    "name": "delete_data",
                    "description": "Delete data from the data store.",
                    "annotations": {
                        "title": "Delete Data",
                        "readOnlyHint": False,
                        "idempotentHint": False,
                        "destructiveHint": True,
                    },
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "The key to delete"
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
