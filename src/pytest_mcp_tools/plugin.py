"""Pytest plugin for MCP tools testing."""

import time

import pytest
import requests
from _pytest.python import Module


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
        help="Run MCP tools tests against the specified base URL",
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

        # Debug logging
        print(f"\n🔍 MCP Tools: Discovering endpoints at {base_url}...")

        # Discover which endpoints exist
        endpoints_found = []
        endpoints_404 = []  # Track which endpoints returned 404
        endpoints_sse_deprecated = []  # Track SSE-based endpoints (406)
        server_ever_reachable = False  # Track if we ever connected to the server

        # First, check if the server is reachable at all
        server_reachable = False
        try:
            # Try root endpoint first
            print(f"   Checking {base_url}...")
            response = requests.get(
                base_url, timeout=2, allow_redirects=False
            )
            if response.status_code < 500:
                server_reachable = True
                server_ever_reachable = True
                print(f"   ✓ Server reachable (status: {response.status_code})")
        except Exception as e:
            print(f"   ✗ Server not reachable: {e}")

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

                except Exception as e:
                    print(f"   ✗ Endpoint {endpoint} not found: {e}")

        # Store discovered endpoints and SSE info
        config._mcp_tools_endpoints = endpoints_found
        config._mcp_tools_sse_deprecated = endpoints_sse_deprecated
        config._mcp_tools_server_unreachable = not server_ever_reachable

        if endpoints_found:
            print(f"✅ MCP Tools: Discovered endpoints: {', '.join(endpoints_found)}\n")
        else:
            if not server_ever_reachable:
                print("❌ MCP Tools: Server unreachable (Connection refused).\n")
                print("   ℹ️  Most MCP servers use stdio transport, not HTTP.")
                print("   This plugin only supports MCP servers with HTTP endpoints.\n")
            else:
                print("❌ MCP Tools: No endpoints discovered! Server is not a valid MCP server.\n")

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

    # Create a virtual module to be parent of all MCP tools test items
    module = Module.from_parent(session, path=session.path)
    module._mcp_tools_virtual_module = True

    # Create a single test that checks if at least one endpoint exists
    test_items = []

    if not endpoints:
        # No endpoints found - create a failing test
        test_id = "test_mcp_tools[NO ENDPOINTS FOUND]"
        sse_deprecated = getattr(config, "_mcp_tools_sse_deprecated", [])
        server_unreachable = getattr(config, "_mcp_tools_server_unreachable", False)

        def make_failing_test(url, sse_endpoints, unreachable):
            def test_func():
                if unreachable:
                    msg = f"Server unreachable at {url} (Connection refused)."
                    msg += "\n\nMost MCP servers use stdio transport, not HTTP."
                    msg += "\nThis plugin only supports MCP servers with HTTP endpoints."
                    msg += "\n\nIf this is an MCP server using stdio, you cannot test it with --mcp-tools."
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
                    except Exception as e:
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
                max_retries = 10
                tools = None
                for retry in range(max_retries):
                    try:
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
                            break
                    except Exception as e:
                        if retry < max_retries - 1:
                            time.sleep(1)
                        else:
                            raise

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

            if http_streaming:
                print("   📡 HTTP streaming support detected")
            if sse:
                print("   📡 SSE support detected (legacy)")


# Use hookimpl with trylast to ensure this runs after terminal reporter
pytest_collection_finish.trylast = True
