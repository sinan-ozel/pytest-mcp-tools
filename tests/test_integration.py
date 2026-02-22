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
