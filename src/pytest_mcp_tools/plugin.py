"""Pytest plugin for MCP tools testing."""

import time

import pytest
import requests
from _pytest.python import Module


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

        # Wait for server to be ready and discover which endpoints exist
        endpoints_found = []
        endpoints_404 = []  # Track which endpoints returned 404
        max_retries = 10
        retry_delay = 1.0

        for retry in range(max_retries):
            # First, check if the server is reachable at all
            server_reachable = False
            try:
                # Try root endpoint first
                print(f"   Retry {retry + 1}/{max_retries}: Checking {base_url}...")
                response = requests.get(
                    base_url, timeout=2, allow_redirects=False
                )
                if response.status_code < 500:
                    server_reachable = True
                    print(f"   ✓ Server reachable (status: {response.status_code})")
            except Exception as e:
                print(f"   ✗ Server not reachable: {e}")

            # If server is reachable, try specific endpoints
            if server_reachable or retry > 3:  # Give server extra time on early retries
                for endpoint in ["/mcp", "/sse", "/messages"]:
                    # Skip this endpoint if we already got 404 for it
                    if endpoint in endpoints_404:
                        continue

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

                        # Only consider endpoint as existing if we get a response that indicates
                        # the endpoint exists (not 404). Acceptable codes:
                        # - 200-299: Success
                        # - 400-499 except 404: Client error (endpoint exists but request invalid)
                        # - 405: Method not allowed (endpoint exists, wrong method)
                        if response.status_code < 500 and response.status_code != 404:
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
                            # Mark this endpoint as 404 so we don't retry it
                            if endpoint not in endpoints_404:
                                endpoints_404.append(endpoint)
                                print(f"   ✗ Endpoint {endpoint} not found (status: 404)")

                    except Exception as e:
                        print(f"   ✗ Endpoint {endpoint} not found: {e}")

            # If we found at least one endpoint, we're done
            if endpoints_found:
                break

            # If all endpoints returned 404, we're done (no need to retry)
            if len(endpoints_404) == 3:  # All three endpoints returned 404
                break

            # Wait before retrying
            if retry < max_retries - 1:
                time.sleep(retry_delay)

        # Store discovered endpoints
        config._mcp_tools_endpoints = endpoints_found

        if endpoints_found:
            print(f"✅ MCP Tools: Discovered endpoints: {', '.join(endpoints_found)}\n")
        else:
            print("❌ MCP Tools: No endpoints discovered! Server is not a valid MCP server.\n")

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

        def make_failing_test(url):
            def test_func():
                pytest.fail(
                    f"No MCP endpoints found at {url}. Expected at least one of: /mcp, /sse, /messages"
                )
            return test_func

        test_func = make_failing_test(base_url)
        test_func.__name__ = test_id

        # Create pytest Function item
        item = pytest.Function.from_parent(
            module,
            name=test_id,
            callobj=test_func,
        )
        item.add_marker(pytest.mark.mcp_tools)
        test_items.append(item)
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

    # Add all MCP tools test items to the collection
    items.extend(test_items)


def pytest_collection_finish(session):
    """Print message about MCP tools tests after collection."""
    config = session.config

    # Only print if we added MCP tools tests
    if hasattr(config, "_mcp_tools_endpoints"):
        endpoints = config._mcp_tools_endpoints
        if endpoints:
            endpoint_list = ", ".join(endpoints)
            print(
                f"\n✅ MCP tools test created for discovered endpoints: {endpoint_list}"
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
