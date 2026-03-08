"""MCP test server for schema-driven test generation.

Exposes tools covering all field types the plugin generates schema-driven cases
for: plain string, number (unconstrained), integer (with min/max), boolean,
enum, and string fields with format keywords (email, uri, date).
All tools accept any valid input and return structuredContent that matches
their outputSchema so every generated test is expected to pass.
"""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route


TOOLS = [
    {
        "name": "echo_string",
        "description": "Echo a text string back.",
        "annotations": {
            "title": "Echo String",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to echo back",
                }
            },
            "required": ["text"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "string",
                    "description": "The echoed text",
                }
            },
        },
    },
    {
        "name": "compute",
        "description": "Double a numeric value.",
        "annotations": {
            "title": "Compute",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "value": {
                    "type": "number",
                    "description": "A numeric value to double",
                }
            },
            "required": ["value"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "result": {
                    "type": "number",
                    "description": "The doubled value",
                }
            },
        },
    },
    {
        "name": "bounded_count",
        "description": "Return an integer within 0 to 100.",
        "annotations": {
            "title": "Bounded Count",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "n": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "description": "Count between 0 and 100",
                }
            },
            "required": ["n"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "count": {
                    "type": "integer",
                    "description": "The returned count",
                }
            },
        },
    },
    {
        "name": "toggle",
        "description": "Toggle a boolean flag.",
        "annotations": {
            "title": "Toggle",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "Whether the feature is enabled",
                }
            },
            "required": ["enabled"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "boolean",
                    "description": "The toggled state",
                }
            },
        },
    },
    {
        "name": "pick",
        "description": "Pick a color from the allowed set.",
        "annotations": {
            "title": "Pick",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": ["red", "green", "blue"],
                    "description": "Color choice",
                }
            },
            "required": ["choice"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "picked": {
                    "type": "string",
                    "description": "The selected color",
                }
            },
        },
    },
    {
        "name": "check_contact",
        "description": "Validate contact information formats.",
        "annotations": {
            "title": "Check Contact",
            "readOnlyHint": True,
        },
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email address",
                },
                "website": {
                    "type": "string",
                    "format": "uri",
                    "description": "Website URL",
                },
                "birthday": {
                    "type": "string",
                    "format": "date",
                    "description": "Birthday date in YYYY-MM-DD format",
                },
            },
            "required": ["email", "website", "birthday"],
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "valid": {
                    "type": "boolean",
                    "description": "Whether the contact info is valid",
                }
            },
        },
    },
]


def _call_tool(name, arguments):
    if name == "echo_string":
        return {
            "content": [{"type": "text", "text": arguments.get("text", "")}],
            "structuredContent": {"result": arguments.get("text", "")},
        }
    if name == "compute":
        value = arguments.get("value", 0)
        return {
            "content": [{"type": "text", "text": str(value * 2)}],
            "structuredContent": {"result": value * 2},
        }
    if name == "bounded_count":
        n = arguments.get("n", 0)
        return {
            "content": [{"type": "text", "text": str(n)}],
            "structuredContent": {"count": n},
        }
    if name == "toggle":
        state = not arguments.get("enabled", False)
        return {
            "content": [{"type": "text", "text": str(state)}],
            "structuredContent": {"state": state},
        }
    if name == "pick":
        choice = arguments.get("choice", "red")
        return {
            "content": [{"type": "text", "text": choice}],
            "structuredContent": {"picked": choice},
        }
    if name == "check_contact":
        return {
            "content": [{"type": "text", "text": "valid"}],
            "structuredContent": {"valid": True},
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
                    "serverInfo": {"name": "schema-driven-server", "version": "0.1.0"},
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
