"""Pytest plugin for MCP tools testing."""

import time

import pytest
import requests
from _pytest.python import Module


def validate_tools_have_names(tools):
    """Validate that all tools have non-empty name fields.

    Args:
        tools: List of tool objects (dicts)

    Raises:
        AssertionError: If any tool is missing name or has empty name
    """
    assert tools, "Expected non-empty tools list"

    for i, tool in enumerate(tools):
        assert "name" in tool, f"Tool at index {i} is missing name field"
        assert tool["name"], f"Tool at index {i} has empty name"


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


def validate_tools_have_titles(tools):
    """Validate that all tools with annotations have a title field.

    Args:
        tools: List of tool objects (dicts)

    Raises:
        AssertionError: If any tool with an annotations field is missing title
    """
    assert tools, "Expected non-empty tools list"

    for tool in tools:
        annotations = tool.get("annotations")
        if annotations is None:
            continue
        tool_name = tool.get("name", "<unknown>")
        assert "title" in annotations, (
            f"Tool '{tool_name}' is missing title in annotations"
        )
        assert annotations["title"], (
            f"Tool '{tool_name}' has empty title in annotations"
        )


_VALID_JSON_SCHEMA_TYPES = frozenset(
    {"string", "number", "integer", "boolean", "array", "object", "null"}
)


def collect_input_schema_missing_descriptions(properties, path=""):
    """Recursively collect paths of fields missing a description in JSON Schema properties.

    Args:
        properties: The ``properties`` dict from a JSON Schema object
        path: Dot-separated path prefix for nested fields (used in recursion)

    Returns:
        List of dotted field-path strings where ``description`` is absent or empty
    """
    missing = []
    for field_name, field_schema in properties.items():
        field_path = f"{path}.{field_name}" if path else field_name
        if not field_schema.get("description"):
            missing.append(field_path)
        nested = field_schema.get("properties")
        if nested:
            missing.extend(
                collect_input_schema_missing_descriptions(nested, field_path)
            )
    return missing


def collect_input_schema_invalid_types(properties, path=""):
    """Recursively collect fields with missing or invalid ``type`` values.

    Valid JSON Schema primitive types are: string, number, integer, boolean,
    array, object, null.

    Args:
        properties: The ``properties`` dict from a JSON Schema object
        path: Dot-separated path prefix for nested fields (used in recursion)

    Returns:
        List of (field_path, actual_type, issue) tuples where issue is
        ``"missing"`` or ``"invalid"``
    """
    invalid = []
    for field_name, field_schema in properties.items():
        field_path = f"{path}.{field_name}" if path else field_name
        field_type = field_schema.get("type")
        if field_type is None:
            invalid.append((field_path, None, "missing"))
        elif isinstance(field_type, str):
            if field_type not in _VALID_JSON_SCHEMA_TYPES:
                invalid.append((field_path, field_type, "invalid"))
        elif isinstance(field_type, list):
            bad = [t for t in field_type if t not in _VALID_JSON_SCHEMA_TYPES]
            if bad:
                invalid.append((field_path, field_type, "invalid"))
        nested = field_schema.get("properties")
        if nested:
            invalid.extend(collect_input_schema_invalid_types(nested, field_path))
    return invalid


def validate_tool_annotations_are_consistent(tools):
    """Validate that readOnlyHint is not true when destructiveHint or idempotentHint
    is true.

    Args:
        tools: List of tool objects (dicts)

    Raises:
        AssertionError: If any tool has readOnlyHint=True combined with
            destructiveHint=True or idempotentHint=True
    """
    assert tools, "Expected non-empty tools list"

    for tool in tools:
        annotations = tool.get("annotations")
        if annotations is None:
            continue
        tool_name = tool.get("name", "<unknown>")
        read_only = annotations.get("readOnlyHint", False)
        destructive = annotations.get("destructiveHint", False)
        idempotent = annotations.get("idempotentHint", False)
        if read_only and destructive:
            assert False, (
                f"Tool '{tool_name}' has readOnlyHint=True and "
                f"destructiveHint=True, which are contradictory"
            )
        if read_only and idempotent:
            assert False, (
                f"Tool '{tool_name}' has readOnlyHint=True and "
                f"idempotentHint=True, which are contradictory"
            )


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
        help="Run MCP tools tests against the specified base URL.",
    )


def pytest_configure(config):
    """Configure pytest with MCP tools marker."""
    config.addinivalue_line(
        "markers",
        "mcp_tools: MCP tools tests",
    )
    config.addinivalue_line(
        "markers",
        "mcp_tools_input_schema: MCP tools per-tool inputSchema field validation tests",
    )

    # If --mcp-tools flag is provided, discover endpoints
    base_url = config.getoption("--mcp-tools")

    if base_url:
        # Store configuration
        config._mcp_tools_base_url = base_url
        config._mcp_tools_http_streaming = False
        config._mcp_tools_sse = False

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

                    # /sse and /messages are deprecated transports.
                    # If they exist (any non-404 response), warn but do not
                    # count them as valid endpoints.
                    if endpoint in ("/sse", "/messages"):
                        if response.status_code == 404:
                            if endpoint not in endpoints_404:
                                endpoints_404.append(endpoint)
                                print(
                                    f"   ✗ Endpoint {endpoint} not found"
                                    f" (status: 404)"
                                )
                        elif response.status_code < 500:
                            if endpoint not in endpoints_sse_deprecated:
                                endpoints_sse_deprecated.append(endpoint)
                                print(
                                    f"   ⚠️  Endpoint {endpoint} is deprecated"
                                    f" (status: {response.status_code})"
                                )
                            if endpoint == "/sse":
                                config._mcp_tools_sse = True
                        continue

                    # /mcp: only consider it as existing if we get a response
                    # that indicates the endpoint exists (not 404). Acceptable:
                    # - 200-299: Success
                    # - 400-499 except 404: Client error (endpoint exists but
                    #   request is malformed)
                    # - 405: Method not allowed (endpoint exists, wrong method)
                    if response.status_code < 500 and response.status_code != 404:
                        if endpoint not in endpoints_found:
                            endpoints_found.append(endpoint)
                            print(
                                f"   ✓ Found endpoint: {endpoint}"
                                f" (status: {response.status_code})"
                            )
                        config._mcp_tools_http_streaming = True
                    elif response.status_code == 404:
                        if endpoint not in endpoints_404:
                            endpoints_404.append(endpoint)
                            print(
                                f"   ✗ Endpoint {endpoint} not found"
                                f" (status: 404)"
                            )
                except requests.exceptions.RequestException as e:
                    print(
                        f"   ✗ Endpoint {endpoint} check failed"
                        f" ({type(e).__name__})"
                    )

        # Store discovered endpoints and SSE info
        config._mcp_tools_endpoints = endpoints_found
        config._mcp_tools_sse_deprecated = endpoints_sse_deprecated
        config._mcp_tools_server_unreachable = not server_ever_reachable

        # Pre-fetch tools to detect whether any have annotations and to store
        # the full tool list for per-tool test generation.
        config._mcp_tools_has_annotations = False
        config._mcp_tools_tools_list = []
        if "/mcp" in endpoints_found:
            try:
                anno_response = requests.post(
                    f"{base_url}/mcp",
                    json={
                        "jsonrpc": "2.0",
                        "method": "tools/list",
                        "id": 1
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                if anno_response.status_code == 200:
                    anno_result = anno_response.json()
                    if (
                        "result" in anno_result
                        and "tools" in anno_result["result"]
                    ):
                        tools_list = anno_result["result"]["tools"]
                        config._mcp_tools_tools_list = tools_list
                        if any("annotations" in t for t in tools_list):
                            config._mcp_tools_has_annotations = True
            except Exception:
                pass

        if endpoints_found:
            print(f"✅ MCP Tools: Discovered endpoints: {', '.join(endpoints_found)}\n")
        else:
            if not server_ever_reachable:
                print("❌ MCP Tools: Server not reachable.\n")
            else:
                print("❌ MCP Tools: No MCP endpoints discovered!\n")

            if endpoints_sse_deprecated:
                print(
                    f"⚠️  Note: Found deprecated endpoints"
                    f" {endpoints_sse_deprecated}."
                )
                print(
                    "   /sse and /messages are no longer supported."
                    " Migrate to /mcp (HTTP streaming).\n"
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
        # No HTTP endpoints found - create a failing test
        test_id = "test_mcp_tools[NO ENDPOINT FOUND]"
        sse_deprecated = getattr(config, "_mcp_tools_sse_deprecated", [])
        server_unreachable = getattr(config, "_mcp_tools_server_unreachable", False)

        def make_failing_test(url, sse_endpoints, unreachable):
            def test_func():
                if unreachable:
                    msg = f"MCP server at {url} is not reachable."
                    msg += "\n\nℹ️  Possible causes:"
                    msg += "\n   - The server is not running"
                    msg += "\n   - Network or configuration issues"
                else:
                    msg = (
                        f"No MCP endpoint found at {url}."
                        f" Expected /mcp (HTTP streaming)."
                    )
                    if sse_endpoints:
                        msg += (
                            f"\n\nFound deprecated endpoints {sse_endpoints}."
                            "\n/sse and /messages are no longer supported."
                            " Migrate to /mcp (HTTP streaming)."
                        )
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

        # Add test_tools_have_names if endpoints were found
        # This tests that all tools have name fields
        def make_tools_have_names_test(url, endpoint="/mcp"):
            def test_tools_have_names():
                """Test that all tools have name fields."""
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

                validate_tools_have_names(tools)
            return test_tools_have_names

        tools_names_test_func = make_tools_have_names_test(base_url)
        tools_names_test_func.__name__ = "test_tools_have_names"

        tools_names_item = pytest.Function.from_parent(
            module,
            name="test_tools_have_names",
            callobj=tools_names_test_func,
        )
        tools_names_item.add_marker(pytest.mark.mcp_tools)
        test_items.append(tools_names_item)

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

        # Add annotation tests only when at least one tool has annotations
        has_annotations = getattr(config, "_mcp_tools_has_annotations", False)
        if has_annotations:
            def make_tools_have_titles_test(url, endpoint="/mcp"):
                def test_tools_have_titles():
                    """Test that all tools with annotations have a title field."""
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

                    validate_tools_have_titles(tools)
                return test_tools_have_titles

            tools_titles_test_func = make_tools_have_titles_test(base_url)
            tools_titles_test_func.__name__ = "test_tools_have_titles"

            tools_titles_item = pytest.Function.from_parent(
                module,
                name="test_tools_have_titles",
                callobj=tools_titles_test_func,
            )
            tools_titles_item.add_marker(pytest.mark.mcp_tools)
            test_items.append(tools_titles_item)

            def make_tool_annotations_are_consistent_test(url, endpoint="/mcp"):
                def test_tool_annotations_are_consistent():
                    """Test that annotation hints are not contradictory.

                    Validates that readOnlyHint is not true when destructiveHint
                    or idempotentHint is true.
                    """
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

                    validate_tool_annotations_are_consistent(tools)
                return test_tool_annotations_are_consistent

            annotations_test_func = make_tool_annotations_are_consistent_test(
                base_url
            )
            annotations_test_func.__name__ = "test_tool_annotations_are_consistent"

            annotations_item = pytest.Function.from_parent(
                module,
                name="test_tool_annotations_are_consistent",
                callobj=annotations_test_func,
            )
            annotations_item.add_marker(pytest.mark.mcp_tools)
            test_items.append(annotations_item)

        # Add per-tool inputSchema field description and type tests.
        # One test per tool, named after the tool, scanning all nested fields.
        tools_list = getattr(config, "_mcp_tools_tools_list", [])
        for tool in tools_list:
            tool_name = tool.get("name", "")
            if not tool_name:
                continue
            input_schema = tool.get("inputSchema", {})
            properties = input_schema.get("properties", {})
            if not properties:
                continue

            # Sanitise the tool name for use as a Python identifier
            safe_name = tool_name.replace("-", "_").replace(" ", "_")

            # --- per-tool description test ---
            def make_tool_field_descriptions_test(url, tname, endpoint="/mcp"):
                def test_func():
                    """Test that every inputSchema field has a description."""
                    response = requests.post(
                        f"{url}{endpoint}",
                        json={
                            "jsonrpc": "2.0",
                            "method": "tools/list",
                            "id": 1
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5,
                    )
                    response.raise_for_status()
                    result = response.json()
                    current_tool = None
                    if "result" in result and "tools" in result["result"]:
                        for t in result["result"]["tools"]:
                            if t.get("name") == tname:
                                current_tool = t
                                break
                    assert current_tool is not None, (
                        f"Tool '{tname}' not found in tools list"
                    )
                    schema_props = (
                        current_tool.get("inputSchema", {}).get("properties", {})
                    )
                    missing = collect_input_schema_missing_descriptions(schema_props)
                    assert not missing, (
                        f"Tool '{tname}' has inputSchema fields missing description: "
                        + ", ".join(missing)
                    )
                return test_func

            desc_test_name = f"test_{safe_name}_input_schema_field_descriptions"
            desc_func = make_tool_field_descriptions_test(base_url, tool_name)
            desc_func.__name__ = desc_test_name
            desc_item = pytest.Function.from_parent(
                module,
                name=desc_test_name,
                callobj=desc_func,
            )
            desc_item.add_marker(pytest.mark.mcp_tools_input_schema)
            test_items.append(desc_item)

            # --- per-tool type test ---
            def make_tool_field_types_test(url, tname, endpoint="/mcp"):
                def test_func():
                    """Test that every inputSchema field has a valid type."""
                    response = requests.post(
                        f"{url}{endpoint}",
                        json={
                            "jsonrpc": "2.0",
                            "method": "tools/list",
                            "id": 1
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=5,
                    )
                    response.raise_for_status()
                    result = response.json()
                    current_tool = None
                    if "result" in result and "tools" in result["result"]:
                        for t in result["result"]["tools"]:
                            if t.get("name") == tname:
                                current_tool = t
                                break
                    assert current_tool is not None, (
                        f"Tool '{tname}' not found in tools list"
                    )
                    schema_props = (
                        current_tool.get("inputSchema", {}).get("properties", {})
                    )
                    invalid = collect_input_schema_invalid_types(schema_props)
                    if invalid:
                        details = "; ".join(
                            f"'{p}' type is {issue} (got {v!r})"
                            for p, v, issue in invalid
                        )
                        assert False, (
                            f"Tool '{tname}' has inputSchema fields with missing or "
                            f"invalid type: {details}"
                        )
                return test_func

            type_test_name = f"test_{safe_name}_input_schema_field_types"
            type_func = make_tool_field_types_test(base_url, tool_name)
            type_func.__name__ = type_test_name
            type_item = pytest.Function.from_parent(
                module,
                name=type_test_name,
                callobj=type_func,
            )
            type_item.add_marker(pytest.mark.mcp_tools_input_schema)
            test_items.append(type_item)

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
            sse = getattr(config, "_mcp_tools_sse", False)

            if sse:
                print("   ⚠️  SSE endpoint detected (deprecated)")


# Use hookimpl with trylast to ensure this runs after terminal reporter
pytest_collection_finish.trylast = True
