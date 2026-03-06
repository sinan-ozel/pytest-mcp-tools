"""MCP test server with a tool whose example omits a required inputSchema field."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


TOOLS = [
    {
        "name": "send_message",
        "description": "Send a message to a recipient.",
        "annotations": {
            "title": "Send Message",
            "readOnlyHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The message text to send",
                },
                "recipient": {
                    "type": "string",
                    "description": "The name of the recipient",
                },
            },
            "required": ["text", "recipient"],
            "examples": [
                # Missing required field "recipient"
                {"text": "Hello"},
            ],
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
                    "serverInfo": {"name": "example-missing-required-server", "version": "0.1.0"},
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
            if name == "send_message":
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": f"Sent: {arguments.get('text', '')}"}],
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
