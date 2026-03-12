"""MCP test server that accepts any tool input without validation.

Used to verify that the plugin's missing-field and wrong-type tests FAIL when
the server does not validate its inputs (i.e., accepts anything and returns
success instead of -32602).

Exposes the same manage_user tool as strict_validation_server but never
validates the arguments — all calls succeed regardless of what is sent.
Unknown methods still return -32601 and invalid requests -32600, so only
the input-validation tests are expected to fail.
"""

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

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
                            "name": "no-validation-server",
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
            # Accept any arguments without validation — always succeed
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": "ok"}],
                    },
                }
            )

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
