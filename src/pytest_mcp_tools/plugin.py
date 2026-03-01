"""Pytest plugin for MCP tools testing."""

import json
import subprocess
import time
from urllib.parse import urlparse

import pytest
import requests
from _pytest.python import Module


def list_tools_stdio(container_name):
    """List available tools from STDIO MCP server.

    Args:
        container_name: The container name or image to communicate with via STDIO

    Returns:
        List of tool names

    Raises:
        ValueError: If the tools list is empty or if communication fails
    """
    try:
        # Get the image name from the running container (if it exists)
        inspect_result = subprocess.run(
            ["docker", "inspect", container_name, "--format", "{{.Config.Image}}"],
            capture_output=True,
            text=True,
            timeout=2
        )

        if inspect_result.returncode == 0 and inspect_result.stdout.strip():
            image_name = inspect_result.stdout.strip()
        else:
            # Container doesn't exist, assume container_name IS the image name
            image_name = container_name

        # MCP STDIO protocol requires initialization handshake
        # Send: initialize request, initialized notification, then tools/list
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 0,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-mcp-tools", "version": "0.1.2"}
                }
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        ]
        input_data = "\n".join(messages) + "\n"

        # Try to run the container in STDIO mode
        result = subprocess.run(
            ["docker", "run", "-i", "--rm", "--network", "none", image_name],
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )

        # If the default command didn't work, try with python server.py
        if result.returncode != 0 or not result.stdout.strip():
            result = subprocess.run(
                ["docker", "run", "-i", "--rm", "--network", "none",
                 "--entrypoint", "python", image_name, "-u", "server.py"],
                input=input_data,
                capture_output=True,
                text=True,
                timeout=10
            )

        if result.returncode == 0 and result.stdout.strip():
            # Parse the response - look for tools/list response (id=1)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                try:
                    response = json.loads(line)
                    # Look for the tools/list response
                    if response.get("id") == 1 and "result" in response and "tools" in response["result"]:
                        tools = response["result"]["tools"]
                        if not tools:
                            raise ValueError("Tools list is empty")
                        return [tool["name"] for tool in tools]
                except json.JSONDecodeError:
                    continue

            raise ValueError(f"No valid tools/list response in output: {result.stdout[:200]}")
        elif result.stderr:
            raise ValueError(f"STDIO server error: {result.stderr[:200]}")
        else:
            raise ValueError("No response from STDIO server")

    except subprocess.TimeoutExpired:
        raise ValueError("STDIO communication timed out")
    except Exception as e:
        raise ValueError(f"STDIO communication error: {e}")


def list_tools_stdio_subprocess(command):
    """List available tools from STDIO MCP server using subprocess.

    This function spawns the server as a subprocess (production-like usage),
    as opposed to list_tools_stdio which uses docker run -i.

    Args:
        command: Command to run the server (e.g., "run-server" or ["python", "server.py"])

    Returns:
        List of tool names

    Raises:
        ValueError: If the tools list is empty or if communication fails
    """
    try:
        # Convert string command to list if needed
        if isinstance(command, str):
            command = [command]

        # MCP STDIO protocol requires initialization handshake
        messages = [
            json.dumps({
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 0,
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-mcp-tools", "version": "0.1.2"}
                }
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }),
            json.dumps({
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            })
        ]
        input_data = "\n".join(messages) + "\n"

        # Run the command as a subprocess
        result = subprocess.run(
            command,
            input=input_data,
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            # Parse the response - look for tools/list response (id=1)
            lines = result.stdout.strip().split('\n')
            for line in lines:
                try:
                    response = json.loads(line)
                    # Look for the tools/list response
                    if response.get("id") == 1 and "result" in response and "tools" in response["result"]:
                        tools = response["result"]["tools"]
                        if not tools:
                            raise ValueError("Tools list is empty")
                        return [tool["name"] for tool in tools]
                except json.JSONDecodeError:
                    continue

            raise ValueError(f"No valid tools/list response in output: {result.stdout[:200]}")
        elif result.stderr:
            raise ValueError(f"STDIO server error: {result.stderr[:200]}")
        else:
            raise ValueError(f"Server exited with code {result.returncode}")

    except subprocess.TimeoutExpired:
        raise ValueError("STDIO communication timed out")
    except FileNotFoundError as e:
        raise ValueError(f"Command not found: {command[0]}")
    except Exception as e:
        raise ValueError(f"STDIO communication error: {e}")


def validate_tools_have_unique_names(tools):
    """Validate that all tools have unique name fields.

    Args:
        tools: List of tool objects (dicts)

    Raises:
        AssertionError: If any two tools share the same name
    """
    assert tools, "Expected non-empty tools list"

    seen = {}
    for i, tool in enumerate(tools):
        name = tool.get("name", f"<unnamed at index {i}>")
        if name in seen:
            assert False, (
                f"Duplicate tool name '{name}' found at indices "
                f"{seen[name]} and {i}"
            )
        seen[name] = i


def list_tools(base_url, endpoint="/mcp"):
    """List available tools from MCP server.

    Args:
        base_url: The base URL of the MCP server
        endpoint: The MCP endpoint to use (default: /mcp)

    Returns:
        List of tool names

    Raises:
        ValueError: If the tools list is empty or if connection fails
    """
    # Try simple HTTP POST with JSON-RPC
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json={
                "jsonrpc": "2.0",
                "method": "tools/list",
                "id": 1
            },
            headers={
                "Content-Type": "application/json",
            },
            timeout=5
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Endpoint {endpoint} not found (404)")
        raise ValueError(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Connection error: {e}")

    result = response.json()

    if "result" in result and "tools" in result["result"]:
        tools = result["result"]["tools"]
        if not tools:
            raise ValueError("Tools list is empty")
        return [tool["name"] for tool in tools]

    raise ValueError(
        f"Missing 'result.tools' in response: {result}"
    )


def pytest_addoption(parser):
    """Add --mcp-tools CLI option."""
    group = parser.getgroup("mcp-tools")
    group.addoption(
        "--mcp-tools",
        action="store",
        metavar="BASE_URL",
        help="Run MCP tools tests against the specified base URL. "
             "Automatically detects HTTP endpoints and STDIO support.",
    )


def pytest_configure(config):
    """Configure pytest with MCP tools marker."""
    config.addinivalue_line(
        "markers",
        "mcp_tools: MCP tools tests",
    )

    # If --mcp-tools flag is provided, discover endpoints
    base_url = config.getoption("--mcp-tools")

    if base_url:
        # Store configuration
        config._mcp_tools_base_url = base_url
        config._mcp_tools_http_streaming = False
        config._mcp_tools_sse = False
        config._mcp_tools_stdio = False
        config._mcp_tools_stdio_command = None

        # Check if this is a stdio:// URL (production-like subprocess usage)
        if base_url.startswith("stdio://"):
            # Extract command from stdio://command format
            command = base_url[8:]  # Remove "stdio://" prefix
            print(f"\n🔍 MCP Tools: Testing STDIO server with command: {command}...")

            try:
                tools = list_tools_stdio_subprocess(command)
                config._mcp_tools_stdio = True
                config._mcp_tools_stdio_command = command
                print(f"✅ MCP Tools: STDIO communication successful ({len(tools)} tool(s) found)\n")
            except Exception as e:
                error_msg = str(e)[:100]
                print(f"❌ MCP Tools: STDIO communication failed: {error_msg}\n")

            # Skip HTTP endpoint discovery for stdio:// URLs
            return

        # Debug logging for HTTP URLs
        print(f"\n🔍 MCP Tools: Discovering endpoints at {base_url}...")

        # Discover which endpoints exist
        endpoints_found = []
        endpoints_404 = []  # Track which endpoints returned 404
        endpoints_sse_deprecated = []  # Track SSE-based endpoints (406)
        server_ever_reachable = False  # Track if we ever connected to the server

        # First, check if the server is reachable at all
        server_reachable = False
        # Try root endpoint first
        print(f"   Checking {base_url}...")
        try:
            response = requests.get(
                base_url, timeout=2, allow_redirects=False
            )
            if response.status_code < 500:
                server_reachable = True
                server_ever_reachable = True
                print(f"   ✓ Server reachable (status: {response.status_code})")
            else:
                print(f"   ✗ Server not reachable at {base_url} (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"   ✗ Server not reachable at {base_url} ({type(e).__name__})")

        # If server is reachable, try specific endpoints
        if server_reachable:
            for endpoint in ["/mcp", "/sse", "/messages"]:
                try:
                    # Use POST for /mcp (JSON-RPC), GET for others
                    if endpoint == "/mcp":
                        response = requests.post(
                            f"{base_url}{endpoint}",
                            json={},
                            timeout=2,
                            allow_redirects=False,
                        )
                    else:
                        response = requests.get(
                            f"{base_url}{endpoint}",
                            timeout=2,
                            allow_redirects=False,
                        )

                    # Check for 406 Not Acceptable (SSE-based MCP, deprecated)
                    if response.status_code == 406:
                        if endpoint not in endpoints_sse_deprecated:
                            endpoints_sse_deprecated.append(endpoint)
                            print(f"   ⚠️  Endpoint {endpoint} uses SSE (deprecated): 406 Not Acceptable")
                    # Only consider endpoint as existing if we get a response that indicates
                    # the endpoint exists (not 404/406). Acceptable codes:
                    # - 200-299: Success
                    # - 400-499 except 404/406: Client error (endpoint exists but request invalid)
                    # - 405: Method not allowed (endpoint exists, wrong method)
                    elif response.status_code < 500 and response.status_code not in (404, 406):
                        if endpoint not in endpoints_found:
                            endpoints_found.append(endpoint)
                            print(f"   ✓ Found endpoint: {endpoint} (status: {response.status_code})")

                        # Set internal toggles
                        if endpoint == "/mcp":
                            config._mcp_tools_http_streaming = True
                        elif endpoint == "/sse":
                            config._mcp_tools_sse = True
                        elif endpoint == "/messages":
                            config._mcp_tools_http_streaming = True
                    elif response.status_code == 404:
                        # Mark this endpoint as 404
                        if endpoint not in endpoints_404:
                            endpoints_404.append(endpoint)
                            print(f"   ✗ Endpoint {endpoint} not found (status: 404)")
                except requests.exceptions.RequestException as e:
                    print(f"   ✗ Endpoint {endpoint} check failed ({type(e).__name__})")

        # Store discovered endpoints and SSE info
        config._mcp_tools_endpoints = endpoints_found
        config._mcp_tools_sse_deprecated = endpoints_sse_deprecated
        config._mcp_tools_server_unreachable = not server_ever_reachable

        # Try to detect STDIO support
        # Extract container name from URL (e.g., http://basic-server:8000 -> basic-server)
        config._mcp_tools_stdio = False
        container_name = None
        if base_url.startswith("http://"):
            # Extract hostname from URL
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            container_name = parsed.hostname

        if container_name:
            print(f"🔍 MCP Tools: Checking STDIO support for {container_name}...")
            try:
                # Check if docker command is available
                docker_check = subprocess.run(
                    ["docker", "--version"],
                    capture_output=True,
                    timeout=1
                )
                if docker_check.returncode != 0:
                    print(f"   ✗ STDIO not available: Docker command not found...")
                else:
                    # Try to list tools via STDIO (spawns new container instance)
                    tools = list_tools_stdio(container_name)
                    config._mcp_tools_stdio = True
                    print(f"   ✓ STDIO communication successful ({len(tools)} tool(s) found)")
            except FileNotFoundError:
                print(f"   ✗ STDIO not available: Docker command not found...")
            except Exception as e:
                error_msg = str(e)[:100]
                print(f"   ✗ STDIO not available: {error_msg}...")

        if endpoints_found:
            print(f"✅ MCP Tools: Discovered endpoints: {', '.join(endpoints_found)}\n")
        else:
            # Check if STDIO was detected
            stdio_available = getattr(config, "_mcp_tools_stdio", False)

            if stdio_available:
                print(f"✅ MCP Tools: STDIO transport detected (HTTP not available)\n")
            elif not server_ever_reachable:
                print("⚠️  MCP Tools: No HTTP endpoints reachable.\n")
                stdio_checked = hasattr(config, "_mcp_tools_stdio")
                if stdio_checked:
                    print("   ℹ️  STDIO transport check also failed.")
                    print("   This container may not support MCP, or requires specific configuration.\n")
                else:
                    print("   ℹ️  Could not determine if STDIO transport is supported.\n")
            else:
                print("❌ MCP Tools: No MCP endpoints discovered!\n")

            if endpoints_sse_deprecated:
                print(f"⚠️  Note: Found SSE-based endpoints {endpoints_sse_deprecated}, but SSE is deprecated.")
                print("   MCP over HTTP with SSE is no longer supported. Use stdio transport instead.\n")

        # Raise warning if SSE is used (legacy)
        if config._mcp_tools_sse:
            print(
                "⚠️  Warning: SSE endpoint detected. SSE is legacy and should be migrated to HTTP streaming."
            )


def pytest_collection_modifyitems(session, config, items):
    """Inject MCP tools test items dynamically into the test collection.

    This hook allows us to add MCP tools tests without requiring a test file.
    """
    # Check if --mcp-tools flag was provided
    base_url = config.getoption("--mcp-tools", default=None)
    if not base_url:
        return

    # Get discovered endpoints
    endpoints = getattr(config, "_mcp_tools_endpoints", [])
    stdio_available = getattr(config, "_mcp_tools_stdio", False)

    # Create a virtual module to be parent of all MCP tools test items
    module = Module.from_parent(session, path=session.path)
    module._mcp_tools_virtual_module = True

    # Create a single test that checks if at least one endpoint exists
    test_items = []

    # If STDIO is available, create STDIO tests even if no HTTP endpoints
    if stdio_available and not endpoints:
        # Check if this is subprocess-based STDIO (stdio:// URL)
        stdio_command = getattr(config, "_mcp_tools_stdio_command", None)

        if stdio_command:
            # Create STDIO presence test
            test_id = "test_mcp_tools[STDIO]"

            def make_stdio_presence_test():
                def test_func():
                    """Test that STDIO transport is available."""
                    # This test passes because we already detected STDIO during pytest_configure
                    pass
                return test_func

            test_func = make_stdio_presence_test()
            test_func.__name__ = test_id

            item = pytest.Function.from_parent(
                module,
                name=test_id,
                callobj=test_func,
            )
            item.add_marker(pytest.mark.mcp_tools)
            test_items.append(item)

            # Create STDIO list_tools test
            def make_stdio_list_tools_test(cmd):
                def test_list_tools_via_stdio():
                    """Test that list_tools function can retrieve tools via STDIO."""
                    tools = list_tools_stdio_subprocess(cmd)
                    assert tools, "Expected non-empty tools list via STDIO"
                return test_list_tools_via_stdio

            stdio_list_func = make_stdio_list_tools_test(stdio_command)
            stdio_list_func.__name__ = "test_list_tools_via_stdio"

            stdio_list_item = pytest.Function.from_parent(
                module,
                name="test_list_tools_via_stdio",
                callobj=stdio_list_func,
            )
            stdio_list_item.add_marker(pytest.mark.mcp_tools)
            test_items.append(stdio_list_item)
        else:
            # Docker-based STDIO (http:// URL with container name)
            # Extract container name from base_url
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            container_name = parsed.hostname

            if container_name:
                # Create STDIO presence test
                test_id = "test_mcp_tools[STDIO]"

                def make_stdio_presence_test():
                    def test_func():
                        """Test that STDIO transport is available."""
                        # This test passes because we already detected STDIO during pytest_configure
                        pass
                    return test_func

                test_func = make_stdio_presence_test()
                test_func.__name__ = test_id

                item = pytest.Function.from_parent(
                    module,
                    name=test_id,
                    callobj=test_func,
                )
                item.add_marker(pytest.mark.mcp_tools)
                test_items.append(item)

                # Create STDIO list_tools test
                def make_stdio_list_tools_test(cname):
                    def test_list_tools_via_stdio():
                        """Test that list_tools function can retrieve tools via STDIO."""
                        tools = list_tools_stdio(cname)
                        assert tools, "Expected non-empty tools list via STDIO"
                    return test_list_tools_via_stdio

                stdio_list_func = make_stdio_list_tools_test(container_name)
                stdio_list_func.__name__ = "test_list_tools_via_stdio"

                stdio_list_item = pytest.Function.from_parent(
                    module,
                    name="test_list_tools_via_stdio",
                    callobj=stdio_list_func,
                )
                stdio_list_item.add_marker(pytest.mark.mcp_tools)
                test_items.append(stdio_list_item)

    elif not endpoints and not stdio_available:
        # No endpoints or STDIO found - create a failing test
        test_id = "test_mcp_tools[NO TRANSPORT FOUND]"
        sse_deprecated = getattr(config, "_mcp_tools_sse_deprecated", [])
        server_unreachable = getattr(config, "_mcp_tools_server_unreachable", False)

        def make_failing_test(url, sse_endpoints, unreachable):
            def test_func():
                if unreachable:
                    msg = f"No transport available for MCP server at {url}."
                    msg += "\n\n• HTTP endpoints: Not reachable (connection refused)"
                    msg += "\n• STDIO transport: Communication failed"
                    msg += "\n\nℹ️  Possible causes:"
                    msg += "\n   - Container is not an MCP server"
                    msg += "\n   - Server requires specific launch parameters"
                    msg += "\n   - Network or configuration issues"
                else:
                    msg = f"No MCP endpoints found at {url}. Expected at least one of: /mcp, /sse, /messages"
                    if sse_endpoints:
                        msg += f"\n\nFound SSE-based endpoints {sse_endpoints}, but SSE is deprecated."
                        msg += "\nMCP over HTTP with SSE is no longer supported. Please use stdio transport instead."
                pytest.fail(msg)
            return test_func

        test_func = make_failing_test(base_url, sse_deprecated, server_unreachable)
        test_func.__name__ = test_id

        # Create pytest Function item
        item = pytest.Function.from_parent(
            module,
            name=test_id,
            callobj=test_func,
        )
        item.add_marker(pytest.mark.mcp_tools)
        test_items.append(item)

        # Add test_list_tools_from_empty_server_raises_error only when server is reachable
        # but has no endpoints (don't add if server is unreachable/stdio-only)
        if not server_unreachable:
            def make_list_tools_error_test(url):
                def test_list_tools_from_empty_server_raises_error():
                    """Test that list_tools raises ValueError when server has no tools."""
                    with pytest.raises(ValueError):
                        list_tools(url, "/mcp")
                return test_list_tools_from_empty_server_raises_error

            error_test_func = make_list_tools_error_test(base_url)
            error_test_func.__name__ = "test_list_tools_from_empty_server_raises_error"

            error_item = pytest.Function.from_parent(
                module,
                name="test_list_tools_from_empty_server_raises_error",
                callobj=error_test_func,
            )
            error_item.add_marker(pytest.mark.mcp_tools)
            test_items.append(error_item)
    else:
        # Format endpoint list for test name
        endpoint_names = "|".join(endpoints)
        test_id = f"test_mcp_tools[POST {endpoint_names}]"

        def make_test_func(url, eps):
            def test_func():
                # Test passes if at least one endpoint was discovered
                if not eps:
                    pytest.fail(
                        f"No MCP endpoints found at {url}. Expected at least one of: /mcp, /sse, /messages"
                    )

            return test_func

        test_func = make_test_func(base_url, endpoints)
        test_func.__name__ = test_id

        # Create pytest Function item
        item = pytest.Function.from_parent(
            module,
            name=test_id,
            callobj=test_func,
        )
        item.add_marker(pytest.mark.mcp_tools)
        test_items.append(item)

        # Add test_list_tools_from_basic_server if endpoints were found
        # This tests that the list_tools function works correctly
        def make_list_tools_test(url, endpoint="/mcp"):
            def test_list_tools_from_basic_server():
                """Test that list_tools function can retrieve tools from the MCP server."""
                max_retries = 10
                tools = None
                for retry in range(max_retries):
                    try:
                        tools = list_tools(url, endpoint)
                        break
                    except Exception:
                        if retry < max_retries - 1:
                            time.sleep(1)
                        else:
                            raise

                assert tools, "Expected non-empty tools list"
            return test_list_tools_from_basic_server

        list_tools_test_func = make_list_tools_test(base_url)
        list_tools_test_func.__name__ = "test_list_tools_from_basic_server"

        list_tools_item = pytest.Function.from_parent(
            module,
            name="test_list_tools_from_basic_server",
            callobj=list_tools_test_func,
        )
        list_tools_item.add_marker(pytest.mark.mcp_tools)
        test_items.append(list_tools_item)

        # Add test_tools_have_descriptions if endpoints were found
        # This tests that all tools have description fields
        def make_tools_have_descriptions_test(url, endpoint="/mcp"):
            def test_tools_have_descriptions():
                """Test that all tools have description fields."""
                tools = None
                response = requests.post(
                    f"{url}{endpoint}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                    timeout=5
                )
                response.raise_for_status()
                result = response.json()

                if "result" in result and "tools" in result["result"]:
                    tools = result["result"]["tools"]

                assert tools, "Expected non-empty tools list"

                # Check each tool has a description
                for tool in tools:
                    tool_name = tool.get("name", "<unknown>")
                    assert "description" in tool, f"Tool '{tool_name}' is missing description field"
                    assert tool["description"], f"Tool '{tool_name}' has empty description"
            return test_tools_have_descriptions

        tools_desc_test_func = make_tools_have_descriptions_test(base_url)
        tools_desc_test_func.__name__ = "test_tools_have_descriptions"

        tools_desc_item = pytest.Function.from_parent(
            module,
            name="test_tools_have_descriptions",
            callobj=tools_desc_test_func,
        )
        tools_desc_item.add_marker(pytest.mark.mcp_tools)
        test_items.append(tools_desc_item)

    # Add STDIO-specific tests if STDIO is supported (and not already added above)
    stdio_supported = getattr(config, "_mcp_tools_stdio", False)
    if stdio_supported and endpoints:  # Only add if we also have HTTP endpoints (hybrid server)
        # Check if this is subprocess-based or docker-based STDIO
        stdio_command = getattr(config, "_mcp_tools_stdio_command", None)

        if stdio_command:
            # Subprocess-based STDIO
            def make_stdio_list_tools_test(cmd):
                def test_list_tools_via_stdio():
                    """Test that list_tools function can retrieve tools via STDIO."""
                    tools = list_tools_stdio_subprocess(cmd)
                    assert tools, "Expected non-empty tools list via STDIO"
                return test_list_tools_via_stdio

            stdio_test_func = make_stdio_list_tools_test(stdio_command)
            stdio_test_func.__name__ = "test_list_tools_via_stdio"

            stdio_item = pytest.Function.from_parent(
                module,
                name="test_list_tools_via_stdio",
                callobj=stdio_test_func,
            )
            stdio_item.add_marker(pytest.mark.mcp_tools)
            test_items.append(stdio_item)
        else:
            # Docker-based STDIO - extract container name from base_url
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            container_name = parsed.hostname

            if container_name:
                # Add test_list_tools_via_stdio
                def make_stdio_list_tools_test(cname):
                    def test_list_tools_via_stdio():
                        """Test that list_tools function can retrieve tools via STDIO."""
                        tools = list_tools_stdio(cname)
                        assert tools, "Expected non-empty tools list via STDIO"
                    return test_list_tools_via_stdio

                stdio_test_func = make_stdio_list_tools_test(container_name)
                stdio_test_func.__name__ = "test_list_tools_via_stdio"

                stdio_item = pytest.Function.from_parent(
                    module,
                    name="test_list_tools_via_stdio",
                    callobj=stdio_test_func,
                )
                stdio_item.add_marker(pytest.mark.mcp_tools)
                test_items.append(stdio_item)

        # Add test_tools_have_unique_names if endpoints were found
        # This tests that all tools have unique name fields
        def make_tools_have_unique_names_test(url, endpoint="/mcp"):
            def test_tools_have_unique_names():
                """Test that all tools have unique name fields."""
                response = requests.post(
                    f"{url}{endpoint}",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={
                        "Content-Type": "application/json",
                    },
                    timeout=5
                )
                response.raise_for_status()
                result = response.json()

                if "result" in result and "tools" in result["result"]:
                    tools = result["result"]["tools"]
                else:
                    tools = []

                validate_tools_have_unique_names(tools)
            return test_tools_have_unique_names

        tools_unique_names_test_func = make_tools_have_unique_names_test(base_url)
        tools_unique_names_test_func.__name__ = "test_tools_have_unique_names"

        tools_unique_names_item = pytest.Function.from_parent(
            module,
            name="test_tools_have_unique_names",
            callobj=tools_unique_names_test_func,
        )
        tools_unique_names_item.add_marker(pytest.mark.mcp_tools)
        test_items.append(tools_unique_names_item)

    # Add all MCP tools test items to the collection
    items.extend(test_items)


def pytest_collection_finish(session):
    """Print message about MCP tools tests after collection."""
    config = session.config

    # Only print if we added MCP tools tests
    if hasattr(config, "_mcp_tools_endpoints"):
        # Count MCP tools tests
        mcp_test_count = sum(
            1 for item in session.items
            if item.get_closest_marker("mcp_tools") is not None
        )

        if mcp_test_count > 0:
            print(f"\ncreated {mcp_test_count} tests")

        endpoints = config._mcp_tools_endpoints
        if endpoints:
            endpoint_list = ", ".join(endpoints)
            print(
                f"✅ MCP tools test created for discovered endpoints: {endpoint_list}"
            )

            # Print status of toggles
            http_streaming = getattr(
                config, "_mcp_tools_http_streaming", False
            )
            sse = getattr(config, "_mcp_tools_sse", False)
            stdio = getattr(config, "_mcp_tools_stdio", False)

            if http_streaming:
                print("   📡 HTTP streaming support detected")
            if sse:
                print("   📡 SSE support detected (legacy)")
            if stdio:
                print("   📡 STDIO transport support detected")


# Use hookimpl with trylast to ensure this runs after terminal reporter
pytest_collection_finish.trylast = True
