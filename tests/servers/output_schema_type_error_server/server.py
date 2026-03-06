"""MCP test server with a tool whose actual output type mismatches outputSchema."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


TOOLS = [
    {
        "name": "get_value",
        "description": "Return a value.",
        "annotations": {
            "title": "Get Value",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {},
            "examples": [
                {},
            ],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "string",
                    "description": "The value (declared as string)",
                }
            },
        },
    },
]


async def health(request):
    return JSONResponse({"status": "ok"})


async def mcp_endpoint(request):
    try:
        body = await request.json()
        method = body.get("method")
        req_id = body.get("id", 1)

        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "output-schema-type-error-server", "version": "0.1.0"},
                },
            })

        if method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            })

        if method == "tools/call":
            req_id = body.get("id", 1)
            # Return integer 42 but outputSchema declares "value" as type "string"
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": "42"}],
                    "structuredContent": {"value": 42},
                },
            })

    except Exception:
        pass

    return JSONResponse(
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
        status_code=400,
    )


app = Starlette(routes=[
    Route('/health', health, methods=['GET']),
    Route('/mcp', mcp_endpoint, methods=['POST']),
])
