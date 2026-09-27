"""MCP test server for schema-driven test generation.

Exposes tools covering all field types the plugin generates schema-driven cases
for: plain string, number (unconstrained), integer (with min/max), boolean,
enum, and string fields with format keywords (email, uri, date).
All tools accept any valid input and return structuredContent that matches
their outputSchema so every generated test is expected to pass.  Invalid input
is rejected with a tool execution error (isError: true), per the MCP spec, so
the plugin's invalid-input tests pass too.
"""

import re

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


_FORMATS = {
    "email": re.compile(r"^[^@]+@[^@]+\.[^@]+$"),
    "uri": re.compile(r"^[a-zA-Z][a-zA-Z0-9+\-.]*://"),
    "date": re.compile(r"^\d{4}-\d{2}-\d{2}$"),
}
_TYPES = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
}


def _validation_error(name, arguments):
    """Return why ``arguments`` violate the tool's inputSchema, or None.

    Checks what the schemas here use: required fields, type, enum, format,
    minimum and maximum.
    """
    tool = next((t for t in TOOLS if t["name"] == name), None)
    if tool is None:
        return None
    schema = tool["inputSchema"]
    for field in schema.get("required", []):
        if field not in arguments:
            return f"missing required field '{field}'"
    for field, value in arguments.items():
        spec = schema["properties"].get(field)
        if spec is None:
            continue
        expected = _TYPES.get(spec.get("type"))
        wrong_bool = isinstance(value, bool) and spec.get("type") != "boolean"
        if expected and (not isinstance(value, expected) or wrong_bool):
            return f"'{field}' must be of type {spec['type']}"
        if "enum" in spec and value not in spec["enum"]:
            return f"'{field}' must be one of {spec['enum']}"
        pattern = _FORMATS.get(spec.get("format"))
        if pattern and not pattern.match(value):
            return f"'{field}' must be a valid {spec['format']}"
        if "minimum" in spec and value < spec["minimum"]:
            return f"'{field}' must be >= {spec['minimum']}"
        if "maximum" in spec and value > spec["maximum"]:
            return f"'{field}' must be <= {spec['maximum']}"
    return None


def _call_tool(name, arguments):
    error = _validation_error(name, arguments)
    if error:
        return {
            "content": [{"type": "text", "text": f"Invalid arguments: {error}"}],
            "isError": True,
        }
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
