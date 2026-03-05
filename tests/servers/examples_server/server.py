"""MCP test server with tools that have examples and outputSchema."""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


TOOLS = [
    {
        "name": "get_greeting",
        "description": "Return a greeting for the given name.",
        "annotations": {
            "title": "Get Greeting",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name to greet",
                }
            },
            "required": ["name"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "greeting": {
                    "type": "string",
                    "description": "The greeting message",
                }
            },
        },
        "examples": [
            {"input": {"name": "World"}},
            {"input": {"name": "Claude"}},
        ],
    },
    {
        "name": "add_numbers",
        "description": "Add two numbers together.",
        "annotations": {
            "title": "Add Numbers",
            "readOnlyHint": False,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "a": {
                    "type": "number",
                    "description": "First number",
                },
                "b": {
                    "type": "number",
                    "description": "Second number",
                },
            },
            "required": ["a", "b"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "number",
                    "description": "The sum",
                }
            },
        },
        "examples": [
            {"input": {"a": 1, "b": 2}},
        ],
    },
    {
        "name": "echo_text",
        "description": "Echo the given text back.",
        "annotations": {
            "title": "Echo Text",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to echo",
                }
            },
            "required": ["text"],
        },
        "examples": [
            {"input": {"text": "hello"}},
        ],
    },
]


def _call_tool(name, arguments):
    if name == "get_greeting":
        greeting = f"Hello, {arguments.get('name', 'World')}!"
        return {
            "content": [{"type": "text", "text": greeting}],
            "structuredContent": {"greeting": greeting},
        }
    if name == "add_numbers":
        result = arguments.get("a", 0) + arguments.get("b", 0)
        return {
            "content": [{"type": "text", "text": str(result)}],
            "structuredContent": {"result": result},
        }
    if name == "echo_text":
        text = arguments.get("text", "")
        return {
            "content": [{"type": "text", "text": text}],
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
                    "serverInfo": {"name": "examples-server", "version": "0.1.0"},
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
