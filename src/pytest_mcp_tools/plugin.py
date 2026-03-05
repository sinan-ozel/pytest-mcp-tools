"""Pytest plugin for MCP tools testing."""

import json
import time

import pytest
import requests
from _pytest.python import Module

_MCP_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def _parse_mcp_response(response):
    """Parse an MCP HTTP response, handling both JSON and SSE (text/event-stream).

    The MCP Streamable HTTP transport allows servers to respond with either
    ``Content-Type: application/json`` or ``Content-Type: text/event-stream``.
    This helper normalises both into a plain dict.

    Args:
        response: A ``requests.Response`` object whose body has been fully read.

    Returns:
        Parsed JSON object (dict).

    Raises:
        ValueError: If SSE response contains no parseable ``data:`` line.
    """
    content_type = response.headers.get("Content-Type", "")
    if "text/event-stream" in content_type:
        for line in response.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                data = line[len("data:"):].strip()
                if data and data != "[DONE]":
                    return json.loads(data)
        raise ValueError("No data found in SSE response")
    return response.json()


def _establish_session(base_url, endpoint="/mcp"):
    """Perform the MCP initialization handshake and return extra request headers.

    Sends an ``initialize`` JSON-RPC request as required by the MCP Streamable
    HTTP transport spec.  If the server returns an ``Mcp-Session-Id`` response
    header the returned dict includes it so callers can attach it to subsequent
    requests.

    Errors are silently ignored: servers that do not require initialization
    will simply ignore or reject the request, and callers fall through to the
    actual tool request without a session header.

    Args:
        base_url: MCP server base URL.
        endpoint: MCP endpoint path (default ``/mcp``).

    Returns:
        Dict of extra headers to include in subsequent requests (may be empty).
    """
    extra = {}
    try:
        response = requests.post(
            f"{base_url}{endpoint}",
            json={
                "jsonrpc": "2.0",
                "method": "initialize",
                "id": 1,
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest-mcp-tools", "version": "0.1.3"},
                },
            },
            headers=_MCP_HEADERS,
            timeout=5,
        )
        session_id = response.headers.get("Mcp-Session-Id")
        if session_id:
            extra = {"Mcp-Session-Id": session_id}
    except Exception:
        pass
    return extra


def _post_tools_list(base_url, endpoint="/mcp"):
    """Send a ``tools/list`` JSON-RPC request, initialising the session if needed.

    Performs the MCP initialization handshake via :func:`_establish_session`
    before sending the actual ``tools/list`` request so that servers
    implementing the full MCP Streamable HTTP spec (which requires
    ``initialize`` before any other method) are handled transparently.

    Args:
        base_url: MCP server base URL.
        endpoint: MCP endpoint path (default ``/mcp``).

    Returns:
        Parsed JSON response dict (may be JSON or SSE-wrapped JSON).

    Raises:
        requests.exceptions.HTTPError: On non-2xx responses.
        requests.exceptions.RequestException: On network-level errors.
    """
    session_extra = _establish_session(base_url, endpoint)
    headers = {**_MCP_HEADERS, **session_extra}
    response = requests.post(
        f"{base_url}{endpoint}",
        json={"jsonrpc": "2.0", "method": "tools/list", "id": 2},
        headers=headers,
        timeout=5,
    )
    response.raise_for_status()
    return _parse_mcp_response(response)


def _post_tools_call(base_url, tool_name, arguments, endpoint="/mcp"):
    """Call a tool via ``tools/call`` JSON-RPC and return the parsed response.

    Performs the MCP initialization handshake (via :func:`_establish_session`)
    before sending the ``tools/call`` request.

    Args:
        base_url: MCP server base URL.
        tool_name: Name of the tool to call.
        arguments: Dict of arguments to pass to the tool.
        endpoint: MCP endpoint path (default ``/mcp``).

    Returns:
        Parsed JSON response dict.

    Raises:
        requests.exceptions.HTTPError: On non-2xx responses.
        requests.exceptions.RequestException: On network-level errors.
    """
    session_extra = _establish_session(base_url, endpoint)
    headers = {**_MCP_HEADERS, **session_extra}
    response = requests.post(
        f"{base_url}{endpoint}",
        json={
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 3,
            "params": {"name": tool_name, "arguments": arguments},
        },
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()
    return _parse_mcp_response(response)


_JSON_SCHEMA_TYPE_TO_PYTHON = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def collect_output_schema_type_mismatches(content, properties, path=""):
    """Recursively collect fields where runtime value type mismatches outputSchema.

    Args:
        content: The ``structuredContent`` dict from a ``tools/call`` response.
        properties: The ``properties`` dict from the tool's ``outputSchema``.
        path: Dot-separated path prefix for nested fields (used in recursion).

    Returns:
        List of (field_path, declared_type, actual_python_type) tuples where
        the actual value's type does not match the declared JSON Schema type.
    """
    mismatches = []
    for field_name, field_schema in properties.items():
        field_path = f"{path}.{field_name}" if path else field_name
        declared_type = field_schema.get("type")
        if declared_type is None or field_name not in content:
            continue
        actual_value = content[field_name]
        expected_python = _JSON_SCHEMA_TYPE_TO_PYTHON.get(declared_type)
        if expected_python is not None:
            # bool is a subclass of int in Python; treat booleans as non-numeric
            if declared_type in ("number", "integer") and isinstance(actual_value, bool):
                mismatches.append(
                    (field_path, declared_type, type(actual_value).__name__)
                )
            elif not isinstance(actual_value, expected_python):
                mismatches.append(
                    (field_path, declared_type, type(actual_value).__name__)
                )
        nested = field_schema.get("properties")
        if nested and isinstance(actual_value, dict):
            mismatches.extend(
                collect_output_schema_type_mismatches(actual_value, nested, field_path)
            )
    return mismatches


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
    try:
        result = _post_tools_list(base_url, endpoint)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise ValueError(f"Endpoint {endpoint} not found (404)")
        raise ValueError(f"HTTP error: {e}")
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Connection error: {e}")

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
    group.addoption(
        "--mcp-tools-production",
        action="store_true",
        default=False,
        help=(
            "When set, only generate example tests for tools with "
            "readOnlyHint=True. Alias of --mcp-tools-read-only."
        ),
    )
    group.addoption(
        "--mcp-tools-read-only",
        action="store_true",
        default=False,
        help=(
            "When set, only generate example tests for tools with "
            "readOnlyHint=True. Alias of --mcp-tools-production."
        ),
    )
    group.addoption(
        "--mcp-tools-strict",
        action="store_true",
        default=False,
        help=(
            "When set, generate failing tests for any tool that lacks "
            "examples or outputSchema."
        ),
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
    config.addinivalue_line(
        "markers",
        "mcp_tools_examples: MCP tools per-tool example call tests",
    )
    config.addinivalue_line(
        "markers",
        "mcp_tools_strict: MCP tools strict-mode compliance tests",
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
                            headers=_MCP_HEADERS,
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
                anno_result = _post_tools_list(base_url, "/mcp")
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
                result = _post_tools_list(url, endpoint)
                tools = result.get("result", {}).get("tools")

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
                result = _post_tools_list(url, endpoint)
                tools = result.get("result", {}).get("tools", [])
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
                result = _post_tools_list(url, endpoint)
                tools = result.get("result", {}).get("tools", [])
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
                    result = _post_tools_list(url, endpoint)
                    tools = result.get("result", {}).get("tools", [])
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
                    result = _post_tools_list(url, endpoint)
                    tools = result.get("result", {}).get("tools", [])
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
                    result = _post_tools_list(url, endpoint)
                    current_tool = next(
                        (t for t in result.get("result", {}).get("tools", [])
                         if t.get("name") == tname),
                        None,
                    )
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
                    result = _post_tools_list(url, endpoint)
                    current_tool = next(
                        (t for t in result.get("result", {}).get("tools", [])
                         if t.get("name") == tname),
                        None,
                    )
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

        # --- per-tool example tests ---
        # Generate one test per example per tool, filtered by readOnlyHint when
        # --mcp-tools-production or --mcp-tools-read-only is set.
        read_only_only = config.getoption(
            "--mcp-tools-production", default=False
        ) or config.getoption("--mcp-tools-read-only", default=False)

        for tool in tools_list:
            tool_name = tool.get("name", "")
            if not tool_name:
                continue
            examples = tool.get("examples", [])
            if not examples:
                continue

            if read_only_only:
                annotations = tool.get("annotations", {}) or {}
                if not annotations.get("readOnlyHint", False):
                    continue

            output_schema = tool.get("outputSchema") or {}
            output_properties = output_schema.get("properties", {})
            safe_name = tool_name.replace("-", "_").replace(" ", "_")

            for idx, example in enumerate(examples):
                example_input = example.get("input", {})
                test_name = f"test_{safe_name}_example_{idx}"

                def make_example_test(url, tname, args, out_props, endpoint="/mcp"):
                    def test_func():
                        """Call tool with example input; validate output against outputSchema."""
                        result = _post_tools_call(url, tname, args, endpoint)
                        assert "error" not in result, (
                            f"Tool '{tname}' call returned JSON-RPC error: "
                            f"{result.get('error')}"
                        )
                        tool_result = result.get("result", {})
                        assert "error" not in tool_result, (
                            f"Tool '{tname}' result contains error: "
                            f"{tool_result.get('error')}"
                        )
                        if out_props:
                            structured = tool_result.get("structuredContent")
                            if structured is not None:
                                mismatches = collect_output_schema_type_mismatches(
                                    structured, out_props
                                )
                                if mismatches:
                                    details = "; ".join(
                                        f"'{p}' declared as {declared} "
                                        f"but got {actual}"
                                        for p, declared, actual in mismatches
                                    )
                                    assert False, (
                                        f"Tool '{tname}' structuredContent type "
                                        f"mismatches outputSchema: {details}"
                                    )
                    return test_func

                example_func = make_example_test(
                    base_url, tool_name, example_input, output_properties
                )
                example_func.__name__ = test_name
                example_item = pytest.Function.from_parent(
                    module,
                    name=test_name,
                    callobj=example_func,
                )
                example_item.add_marker(pytest.mark.mcp_tools_examples)
                test_items.append(example_item)

        # --- strict-mode compliance tests ---
        # When --mcp-tools-strict is set, generate per-tool tests that fail
        # if any tool is missing examples or outputSchema.
        if config.getoption("--mcp-tools-strict", default=False):
            for tool in tools_list:
                tool_name = tool.get("name", "")
                if not tool_name:
                    continue
                safe_name = tool_name.replace("-", "_").replace(" ", "_")

                # --- has_examples test ---
                def make_has_examples_test(tname):
                    def test_func():
                        """Fail if the tool declares no examples."""
                        assert False, (
                            f"Tool '{tname}' has no examples. "
                            "Add at least one entry to the 'examples' list."
                        )
                    return test_func

                def make_has_examples_pass(tname):
                    def test_func():
                        """Pass: the tool declares at least one example."""
                        pass
                    return test_func

                has_examples = bool(tool.get("examples"))
                examples_test_name = f"test_{safe_name}_has_examples"
                examples_func = (
                    make_has_examples_pass(tool_name)
                    if has_examples
                    else make_has_examples_test(tool_name)
                )
                examples_func.__name__ = examples_test_name
                examples_item = pytest.Function.from_parent(
                    module,
                    name=examples_test_name,
                    callobj=examples_func,
                )
                examples_item.add_marker(pytest.mark.mcp_tools_strict)
                test_items.append(examples_item)

                # --- has_output_schema test ---
                def make_has_output_schema_test(tname):
                    def test_func():
                        """Fail if the tool declares no outputSchema."""
                        assert False, (
                            f"Tool '{tname}' has no outputSchema. "
                            "Add an 'outputSchema' object to the tool definition."
                        )
                    return test_func

                def make_has_output_schema_pass(tname):
                    def test_func():
                        """Pass: the tool declares an outputSchema."""
                        pass
                    return test_func

                has_output_schema = bool(tool.get("outputSchema"))
                schema_test_name = f"test_{safe_name}_has_output_schema"
                schema_func = (
                    make_has_output_schema_pass(tool_name)
                    if has_output_schema
                    else make_has_output_schema_test(tool_name)
                )
                schema_func.__name__ = schema_test_name
                schema_item = pytest.Function.from_parent(
                    module,
                    name=schema_test_name,
                    callobj=schema_func,
                )
                schema_item.add_marker(pytest.mark.mcp_tools_strict)
                test_items.append(schema_item)

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
