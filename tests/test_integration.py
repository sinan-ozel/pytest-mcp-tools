"""Integration tests for pytest-mcp-tools CLI functionality."""

import subprocess
import time
import pytest


def test_mcp_tools_flag_is_recognized():
    """Test that --mcp-tools flag is recognized by pytest (plugin is loaded).

    This test verifies that the pytest-mcp-tools plugin is properly installed
    and the --mcp-tools flag is available.
    """
    print("\n🔍 Testing if --mcp-tools flag is recognized...", flush=True)

    # Give the MCP server time to start up
    time.sleep(2)

    # Run pytest with --mcp-tools flag
    result = subprocess.run(
        ["pytest", "--mcp-tools=http://basic-server:8000", "-v"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    # Check that the flag is NOT unrecognized
    output = result.stdout

    assert (
        "unrecognized arguments: --mcp-tools" not in output
    ), f"Plugin not loaded: --mcp-tools flag not recognized. Output:\n{output}"

    print("✅ --mcp-tools flag is recognized", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_basic_mcp_server_tools_discovered():
    """Test that MCP tools are discovered and tests are generated.

    This test verifies that the plugin:
    1. Discovers MCP tools from the server
    2. Generates test items for each tool
    3. Tests appear in pytest's output with the expected format

    Expected test format: test_mcp_tools[POST /mcp|/sse|/messages]
    """
    print("\n🔍 Testing MCP tools discovery and test generation...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://basic-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that MCP tools test was discovered and appears in output
    # Accept any endpoint pattern
    assert (
        "test_mcp_tools[POST" in output
    ), f"Expected test_mcp_tools[POST ...] in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that regular tests also ran
    assert (
        "test_samples" in output
    ), f"Expected regular test files to be collected, got:\n{output}"

    # Check that some tests passed
    assert (
        "passed" in output.lower() or "PASSED" in output
    ), f"Expected some tests to pass, got:\n{output}"

    print("✅ MCP tools discovered and tests generated", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_mcp_tools_run_alongside_regular_tests():
    """Test that --mcp-tools flag allows regular pytest tests to run alongside MCP tests.

    This ensures the plugin integrates properly with pytest's test collection
    and doesn't interfere with normal pytest operation.
    """
    print(
        "\n🔍 Testing MCP tools plugin with regular pytest tests...", flush=True
    )
    time.sleep(0.5)

    # This test expects that there are regular test files in /app/test_samples/
    # The plugin should:
    # 1. Run MCP tools tests
    # 2. Then allow pytest to continue and run regular tests
    result = subprocess.run(
        [
            "pytest",
            "--mcp-tools=http://basic-server:8000",
            "/app/test_samples/",
            "-v",
        ],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout

    # Check that /mcp endpoint is found
    assert (
        "Found endpoint: /mcp" in output
    ), f"Expected /mcp endpoint to be found, got:\n{output}"

    # Check that /sse endpoint is not found (404)
    assert (
        "Endpoint /sse not found" in output
    ), f"Expected /sse endpoint not found, got:\n{output}"

    # Check that regular tests were collected and ran
    assert (
        "test_sample_addition" in output or "test_samples" in output
    ), f"Expected regular test files to be collected, got:\n{output}"

    # Check that regular tests passed
    assert (
        "test_sample_addition" in output or "PASSED" in output
    ), f"Expected regular tests to pass, got:\n{output}"

    print("✅ MCP tools and regular tests run together", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_empty_server_all_endpoints_404():
    """Test that a server with no MCP endpoints returns 404 for all endpoint checks.

    This test verifies that when a server has no MCP endpoints:
    1. All 3 MCP endpoints (POST /mcp, /sse, /messages) return 404
    2. The plugin reports no endpoints discovered
    3. No MCP test is created
    """
    print("\n🔍 Testing server with no MCP endpoints (all 404)...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://empty-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that all 3 endpoints were not found (404)
    assert (
        "Endpoint /mcp not found" in output
    ), f"Expected /mcp endpoint not found, got:\n{output}\n\nSTDERR:\n{stderr}"

    assert (
        "Endpoint /sse not found" in output
    ), f"Expected /sse endpoint not found, got:\n{output}\n\nSTDERR:\n{stderr}"

    assert (
        "Endpoint /messages not found" in output
    ), f"Expected /messages endpoint not found, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that no endpoints were discovered
    assert (
        "No endpoints discovered" in output
    ), f"Expected 'No endpoints discovered' message, got:\n{output}"

    # Check that a failing test was created
    assert (
        "test_mcp_tools[NO ENDPOINTS FOUND]" in output or "FAILED" in output
    ), f"Expected failing test to be created, got:\n{output}"

    # Check that pytest exited with error code when no endpoints found
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail (exit code != 0) when no endpoints found, got exit code: {result.returncode}"

    print("✅ Empty server test shows all endpoints 404, pytest failed as expected", flush=True)


@pytest.mark.depends(on=["test_basic_mcp_server_tools_discovered"])
def test_list_tools_from_basic_server():
    """Test that the dynamically generated test_list_tools_from_basic_server passes.

    This test verifies that when --mcp-tools is used with a server that has endpoints,
    the plugin generates and runs a test_list_tools_from_basic_server test that passes.
    """
    print("\n🔍 Testing dynamically generated list_tools test with basic server...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://basic-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_list_tools_from_basic_server was created and ran
    assert (
        "test_list_tools_from_basic_server" in output
    ), f"Expected test_list_tools_from_basic_server in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed
    assert (
        "PASSED" in output and "test_list_tools_from_basic_server" in output
    ), f"Expected test_list_tools_from_basic_server to pass, got:\n{output}"

    print("✅ Dynamically generated list_tools test passed for basic server", flush=True)


@pytest.mark.depends(on=["test_empty_server_all_endpoints_404"])
def test_list_tools_from_empty_server_raises_error():
    """Test that the dynamically generated test_list_tools_from_empty_server_raises_error passes.

    This test verifies that when --mcp-tools is used with a server that has no endpoints,
    the plugin generates and runs a test_list_tools_from_empty_server_raises_error test that passes.
    """
    print("\n🔍 Testing dynamically generated list_tools error test with empty server...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://empty-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_list_tools_from_empty_server_raises_error was created and ran
    assert (
        "test_list_tools_from_empty_server_raises_error" in output
    ), f"Expected test_list_tools_from_empty_server_raises_error in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed (it should pass because it expects an error)
    assert (
        "PASSED" in output and "test_list_tools_from_empty_server_raises_error" in output
    ), f"Expected test_list_tools_from_empty_server_raises_error to pass, got:\n{output}"

    print("✅ Dynamically generated list_tools error test passed for empty server", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_sse_server_deprecation_warning():
    """Test that SSE-based MCP servers show deprecation warning.

    This test verifies that when a server uses the deprecated HTTP/SSE transport:
    1. The endpoint returns 406 Not Acceptable (SSE requires specific headers)
    2. The plugin detects this as a deprecated SSE endpoint
    3. A clear deprecation message is shown
    4. The test fails with helpful guidance to use stdio instead
    """
    print("\n🔍 Testing SSE server deprecation warning...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://sse-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that SSE deprecation warning appears during discovery
    assert (
        "uses SSE (deprecated)" in output or "406 Not Acceptable" in output
    ), f"Expected SSE deprecation warning during discovery, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the final message mentions SSE deprecation
    assert (
        "SSE is deprecated" in output or "stdio transport" in output
    ), f"Expected SSE deprecation message in failure, got:\n{output}"

    # Check that no valid endpoints were found (SSE is not supported)
    assert (
        "No MCP endpoints found" in output or "NO ENDPOINTS FOUND" in output
    ), f"Expected no endpoints found message, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail when only SSE endpoints found, got exit code: {result.returncode}"

    print("✅ SSE server correctly shows deprecation warning", flush=True)


@pytest.mark.depends(on=["test_basic_mcp_server_tools_discovered"])
def test_tools_have_descriptions_passes_with_basic_server():
    """Test that the test_tools_have_descriptions test passes when tools have descriptions.

    This test verifies that when tools have proper description fields,
    the dynamically generated test_tools_have_descriptions test passes.
    """
    print("\n🔍 Testing tools have descriptions check with basic server...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://basic-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_descriptions was created and ran
    assert (
        "test_tools_have_descriptions" in output
    ), f"Expected test_tools_have_descriptions in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed
    assert (
        "PASSED" in output and "test_tools_have_descriptions" in output
    ), f"Expected test_tools_have_descriptions to pass, got:\n{output}"

    print("✅ test_tools_have_descriptions passed for basic server with descriptions", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tools_have_descriptions_fails_without_descriptions():
    """Test that the test_tools_have_descriptions test fails when tools lack descriptions.

    This test verifies that when tools are missing description fields,
    the dynamically generated test_tools_have_descriptions test fails with a clear message.
    """
    print("\n🔍 Testing tools have descriptions check with server missing descriptions...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://no-descriptions-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_descriptions was created and ran
    assert (
        "test_tools_have_descriptions" in output
    ), f"Expected test_tools_have_descriptions in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test failed
    assert (
        "FAILED" in output and "test_tools_have_descriptions" in output
    ), f"Expected test_tools_have_descriptions to fail, got:\n{output}"

    # Check that the failure message mentions missing description
    assert (
        "missing description" in output.lower() or "description field" in output.lower()
    ), f"Expected failure message about missing description, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail when descriptions are missing, got exit code: {result.returncode}"

    print("✅ test_tools_have_descriptions correctly failed for server without descriptions", flush=True)


@pytest.mark.depends(on=["test_basic_mcp_server_tools_discovered"])
def test_created_tests_message():
    """Test that the 'created X tests' message appears after collection.

    This test verifies that after pytest collects tests with --mcp-tools,
    it displays a message showing how many tests were created.
    """
    print("\n🔍 Testing 'created X tests' message...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://basic-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that "created X tests" message appears
    assert (
        "created 3 tests" in output
    ), f"Expected 'created 3 tests' message in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    print("✅ 'created 3 tests' message appears correctly", flush=True)
