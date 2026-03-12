"""MCP test server that strictly validates tool inputs and returns proper JSON-RPC errors.

Used to test that the plugin correctly detects when a server returns -32602 for
missing required fields or wrong-typed values, -32600 for invalid requests, and
-32601 for unknown methods.

Tool: manage_user
  username  string (no format)         required
  age       integer                    required
  email     string format "email"      required
  role      string enum admin/editor/viewer  required
"""
import re

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

TOOLS = [
    {
        "name": "manage_user",
        "description": "Create or update a user record.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The username",
                },
                "age": {
                    "type": "integer",
                    "description": "Age in years",
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "Email address",
                },
                "role": {
                    "type": "string",
                    "enum": ["admin", "editor", "viewer"],
                    "description": "User role",
                },
            },
            "required": ["username", "age", "email", "role"],
        },
    }
]


def _invalid_params(req_id, message):
    return JSONResponse(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32602, "message": f"Invalid params: {message}"},
        }
    )


def _validate_manage_user(arguments, req_id):
    required = ["username", "age", "email", "role"]
    for field in required:
        if field not in arguments:
            return _invalid_params(req_id, f"missing required field '{field}'")

    username = arguments["username"]
    if not isinstance(username, str) or isinstance(username, bool):
        return _invalid_params(req_id, "'username' must be a string")

    age = arguments["age"]
    if not isinstance(age, int) or isinstance(age, bool):
        return _invalid_params(req_id, "'age' must be an integer")

    email = arguments["email"]
    if not isinstance(email, str) or not _EMAIL_RE.match(email):
        return _invalid_params(req_id, "'email' must be a valid email address")

    role = arguments["role"]
    if role not in ("admin", "editor", "viewer"):
        return _invalid_params(req_id, f"'role' must be one of admin, editor, viewer; got '{role}'")

    return None


async def health(request):
    return JSONResponse({"status": "ok"})


async def mcp_endpoint(request):
    try:
        body = await request.json()
        method = body.get("method")
        req_id = body.get("id", 1)

        if method == "initialize":
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": "2025-03-26",
                        "capabilities": {"tools": {}},
                        "serverInfo": {
                            "name": "strict-validation-server",
                            "version": "0.1.0",
                        },
                    },
                }
            )

        if method == "tools/list":
            return JSONResponse(
                {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}
            )

        if method == "tools/call":
            params = body.get("params")
            if params is None or not isinstance(params, dict):
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {
                            "code": -32600,
                            "message": "Invalid Request: params must be an object",
                        },
                    },
                    status_code=400,
                )

            name = params.get("name")
            arguments = params.get("arguments", {})

            if name == "manage_user":
                error_response = _validate_manage_user(arguments, req_id)
                if error_response is not None:
                    return error_response
                return JSONResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"User {arguments['username']} managed",
                                }
                            ]
                        },
                    }
                )

            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": "Method not found"},
                }
            )

        # Unknown method
        if method is not None:
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": "Method not found"},
                }
            )

    except Exception:
        pass

    return JSONResponse(
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
        status_code=400,
    )


app = Starlette(
    routes=[
        Route("/health", health, methods=["GET"]),
        Route("/mcp", mcp_endpoint, methods=["POST"]),
    ]
)
