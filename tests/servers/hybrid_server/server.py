"""Hybrid MCP server supporting both HTTP and STDIO transports."""

import sys
import json
import os
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

# Tool definitions shared between HTTP and STDIO
TOOLS = [
    {
        "name": "hybrid_tool",
        "description": "A tool that works via both HTTP and STDIO.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "description": "The action to perform"
                }
            },
            "required": ["action"]
        }
    }
]

def handle_tools_list(request_id=1):
    """Return the list of tools."""
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {"tools": TOOLS}
    }

# ===== STDIO MODE =====
def stdio_mode():
    """Run in STDIO mode - read from stdin, write to stdout."""
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            
            if method == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", 0),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {"listChanged": False}
                        },
                        "serverInfo": {
                            "name": "hybrid-test-server",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(response), flush=True)
            elif method == "notifications/initialized":
                # Notifications don't require a response
                pass
            elif method == "tools/list":
                response = handle_tools_list(request.get("id", 1))
                print(json.dumps(response), flush=True)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id", 1),
                    "error": {
                        "code": -32601,
                        "message": "Method not found"
                    }
                }
                print(json.dumps(response), flush=True)
        except json.JSONDecodeError:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

# ===== HTTP MODE =====
async def health(request):
    """Health check endpoint."""
    return JSONResponse({"status": "ok"})

async def list_tools_endpoint(request):
    """Handle JSON-RPC tools/list requests via HTTP."""
    try:
        body = await request.json()
        if body.get("method") == "tools/list":
            response = handle_tools_list(body.get("id", 1))
            return JSONResponse(response)
    except Exception:
        pass
    
    return JSONResponse(
        {"jsonrpc": "2.0", "error": {"code": -32600, "message": "Invalid Request"}},
        status_code=400
    )

# Create Starlette app for HTTP mode
app = Starlette(routes=[
    Route('/health', health, methods=['GET']),
    Route('/mcp', list_tools_endpoint, methods=['POST']),
])

# Entry point
if __name__ == "__main__":
    # Check if we should run in STDIO mode or HTTP mode
    # STDIO mode: python server.py
    # HTTP mode: uvicorn server:app
    mode = os.getenv("MCP_MODE", "stdio")
    if mode == "stdio":
        stdio_mode()
    else:
        # This shouldn't be reached when using uvicorn
        print("Use uvicorn to run in HTTP mode: uvicorn server:app --host 0.0.0.0 --port 8000", file=sys.stderr)
        sys.exit(1)
