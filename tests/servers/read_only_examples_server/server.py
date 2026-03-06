"""MCP test server with one readOnly and one non-readOnly tool, each with examples."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


TOOLS = [
    {
        "name": "fetch_info",
        "description": "Fetch read-only information.",
        "annotations": {
            "title": "Fetch Info",
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
                "info": {
                    "type": "string",
                    "description": "The fetched information",
                }
            },
        },
    },
    {
        "name": "mutate_data",
        "description": "Mutate data in the store.",
        "annotations": {
            "title": "Mutate Data",
            "readOnlyHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The key to mutate",
                }
            },
            "required": ["key"],
            "examples": [
                {"key": "test"},
            ],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Operation status",
                }
            },
        },
    },
]


def _call_tool(name, arguments):
    if name == "fetch_info":
        return {
            "content": [{"type": "text", "text": "some info"}],
            "structuredContent": {"info": "some info"},
        }
    if name == "mutate_data":
        return {
            "content": [{"type": "text", "text": "ok"}],
            "structuredContent": {"status": "ok"},
        }
    return {"content": [{"type": "text", "text": "unknown tool"}]}


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
                    "serverInfo": {"name": "read-only-examples-server", "version": "0.1.0"},
                },
            })

        if method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS},
            })

        if method == "tools/call":
            params = body.get("params", {})
            name = params.get("name")
            arguments = params.get("arguments", {})
            result = _call_tool(name, arguments)
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
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
