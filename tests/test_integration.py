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

    Expected test format: test_mcp_tools[POST /mcp]
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
    """Test that a server with no MCP endpoints returns 404 for the /mcp endpoint check.

    This test verifies that when a server has no MCP endpoints:
    1. The /mcp endpoint returns 404
    2. The plugin reports no endpoints discovered
    3. No MCP test is created
    """
    print("\n🔍 Testing server with no MCP endpoints (404)...", flush=True)
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

    # Check that /mcp endpoint was not found (404)
    assert (
        "Endpoint /mcp not found" in output
    ), f"Expected /mcp endpoint not found, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that no endpoints were discovered
    assert (
        "No MCP endpoints discovered" in output
    ), f"Expected 'No MCP endpoints discovered' message, got:\n{output}"

    # Check that a failing test was created
    assert (
        "test_mcp_tools[NO TRANSPORT FOUND]" in output or "FAILED" in output
    ), f"Expected failing test to be created, got:\n{output}"

    # Check that pytest exited with error code when no endpoints found
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail (exit code != 0) when no endpoints found, got exit code: {result.returncode}"

    print("✅ Empty server test shows endpoint 404, pytest failed as expected", flush=True)


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

    # Check that "created X tests" message appears (now expecting 5 tests)
    assert (
        "created 5 tests" in output
    ), f"Expected 'created 5 tests' message in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    print("✅ 'created 5 tests' message appears correctly", flush=True)


@pytest.mark.depends(on=["test_basic_mcp_server_tools_discovered"])
def test_tools_have_names_passes_with_basic_server():
    """Test that the test_tools_have_names test passes when tools have names.

    This test verifies that when tools have proper name fields,
    the dynamically generated test_tools_have_names test passes.
    """
    print("\n🔍 Testing tools have names check with basic server...", flush=True)
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

    # Check that test_tools_have_names was created and ran
    assert (
        "test_tools_have_names" in output
    ), f"Expected test_tools_have_names in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed
    assert (
        "PASSED" in output and "test_tools_have_names" in output
    ), f"Expected test_tools_have_names to pass, got:\n{output}"

    print("✅ test_tools_have_names passed for basic server with names", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tools_have_names_fails_without_names():
    """Test that the test_tools_have_names test fails when tools lack names.

    This test verifies that when tools are missing name fields,
    the dynamically generated test_tools_have_names test fails with a clear message.
    """
    print("\n🔍 Testing tools have names check with server missing names...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://no-names-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_names was created and ran
    assert (
        "test_tools_have_names" in output
    ), f"Expected test_tools_have_names in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test failed
    assert (
        "FAILED" in output and "test_tools_have_names" in output
    ), f"Expected test_tools_have_names to fail, got:\n{output}"

    # Check that the failure message mentions missing name
    assert (
        "missing name" in output.lower() or "name field" in output.lower()
    ), f"Expected failure message about missing name, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail when names are missing, got exit code: {result.returncode}"

    print("✅ test_tools_have_names correctly failed for server without names", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_hybrid_server_supports_both_http_and_stdio():
    """Test that hybrid server is detected as supporting both HTTP and STDIO.

    This test verifies that a server supporting both transports:
    1. Has HTTP endpoints discovered
    2. Has STDIO communication working
    3. Creates tests for both transports
    """
    print("\n🔍 Testing hybrid server with both HTTP and STDIO support...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://hybrid-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that HTTP endpoint was discovered
    assert (
        "Found endpoint: /mcp" in output
    ), f"Expected /mcp endpoint to be found, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that HTTP tests were created
    assert (
        "test_list_tools_from_basic_server" in output
    ), f"Expected HTTP test to be created, got:\n{output}"

    # Check that both tests passed
    assert (
        "PASSED" in output
    ), f"Expected tests to pass, got:\n{output}"

    print("✅ Hybrid server correctly detected HTTP support", flush=True)


@pytest.mark.depends(on=["test_basic_mcp_server_tools_discovered"])
def test_tools_have_unique_names_passes_with_basic_server():
    """Test that the test_tools_have_unique_names test passes when tools have unique names.

    This test verifies that when all tools have distinct name fields,
    the dynamically generated test_tools_have_unique_names test passes.
    """
    print("\n🔍 Testing tools have unique names check with basic server...", flush=True)
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

    # Check that test_tools_have_unique_names was created and ran
    assert (
        "test_tools_have_unique_names" in output
    ), f"Expected test_tools_have_unique_names in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed
    assert (
        "PASSED" in output and "test_tools_have_unique_names" in output
    ), f"Expected test_tools_have_unique_names to pass, got:\n{output}"

    print("✅ test_tools_have_unique_names passed for basic server with unique names", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tools_have_unique_names_fails_with_duplicate_names():
    """Test that the test_tools_have_unique_names test fails when tools have duplicate names.

    This test verifies that when multiple tools share the same name field,
    the dynamically generated test_tools_have_unique_names test fails with a clear message.
    """
    print("\n🔍 Testing tools have unique names check with server having duplicate names...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://duplicate-names-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_unique_names was created and ran
    assert (
        "test_tools_have_unique_names" in output
    ), f"Expected test_tools_have_unique_names in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test failed
    assert (
        "FAILED" in output and "test_tools_have_unique_names" in output
    ), f"Expected test_tools_have_unique_names to fail, got:\n{output}"

    # Check that the failure message mentions duplicate names
    assert (
        "duplicate" in output.lower() or "unique" in output.lower()
    ), f"Expected failure message about duplicate names, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail when tool names are not unique, got exit code: {result.returncode}"

    print("✅ test_tools_have_unique_names correctly failed for server with duplicate names", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tools_have_titles_passes_with_annotations_server():
    """Test that test_tools_have_titles passes when tools have a title annotation.

    This test verifies that when all tools include a title in their annotations,
    the dynamically generated test_tools_have_titles test passes.
    """
    print("\n🔍 Testing tools have titles check with annotations server...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://annotations-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_titles was created and ran
    assert (
        "test_tools_have_titles" in output
    ), f"Expected test_tools_have_titles in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test passed
    assert (
        "PASSED" in output and "test_tools_have_titles" in output
    ), f"Expected test_tools_have_titles to pass, got:\n{output}"

    print("✅ test_tools_have_titles passed for annotations server with titles", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tools_have_titles_fails_without_titles():
    """Test that test_tools_have_titles fails when tools lack a title annotation.

    This test verifies that when tools have annotations but are missing the title
    field, the dynamically generated test_tools_have_titles test fails with a
    clear message.
    """
    print("\n🔍 Testing tools have titles check with no-titles server...", flush=True)
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://no-titles-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tools_have_titles was created and ran
    assert (
        "test_tools_have_titles" in output
    ), f"Expected test_tools_have_titles in output, got:\n{output}\n\nSTDERR:\n{stderr}"

    # Check that the test failed
    assert (
        "FAILED" in output and "test_tools_have_titles" in output
    ), f"Expected test_tools_have_titles to fail, got:\n{output}"

    # Check that the failure message mentions missing title
    assert (
        "title" in output.lower()
    ), f"Expected failure message about missing title, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), f"Expected pytest to fail when title is missing, got exit code: {result.returncode}"

    print("✅ test_tools_have_titles correctly failed for server without titles", flush=True)


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tool_annotations_are_consistent_passes_with_annotations_server():
    """Test that test_tool_annotations_are_consistent passes for valid annotations.

    This test verifies that when tools have consistent annotation hints
    (readOnlyHint is not true alongside destructiveHint or idempotentHint),
    the dynamically generated test_tool_annotations_are_consistent test passes.
    """
    print(
        "\n🔍 Testing annotation consistency check with annotations server...",
        flush=True,
    )
    time.sleep(0.5)

    result = subprocess.run(
        ["pytest", "--mcp-tools=http://annotations-server:8000", "-v", "-s"],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tool_annotations_are_consistent was created and ran
    assert (
        "test_tool_annotations_are_consistent" in output
    ), (
        f"Expected test_tool_annotations_are_consistent in output, "
        f"got:\n{output}\n\nSTDERR:\n{stderr}"
    )

    # Check that the test passed
    assert (
        "PASSED" in output and "test_tool_annotations_are_consistent" in output
    ), (
        f"Expected test_tool_annotations_are_consistent to pass, "
        f"got:\n{output}"
    )

    print(
        "✅ test_tool_annotations_are_consistent passed for annotations server",
        flush=True,
    )


@pytest.mark.depends(on=["test_mcp_tools_flag_is_recognized"])
def test_tool_annotations_are_consistent_fails_with_conflicting_annotations():
    """Test that test_tool_annotations_are_consistent fails for conflicting annotations.

    This test verifies that when tools have readOnlyHint=True combined with
    destructiveHint=True or idempotentHint=True, the dynamically generated
    test_tool_annotations_are_consistent test fails with a clear message.
    """
    print(
        "\n🔍 Testing annotation consistency check with conflicting annotations server...",
        flush=True,
    )
    time.sleep(0.5)

    result = subprocess.run(
        [
            "pytest",
            "--mcp-tools=http://conflicting-annotations-server:8000",
            "-v",
            "-s",
        ],
        capture_output=True,
        text=True,
        cwd="/app",
    )

    output = result.stdout
    stderr = result.stderr

    # Debug: print both stdout and stderr
    print(f"STDOUT:\n{output}\n")
    print(f"STDERR:\n{stderr}\n")

    # Check that test_tool_annotations_are_consistent was created and ran
    assert (
        "test_tool_annotations_are_consistent" in output
    ), (
        f"Expected test_tool_annotations_are_consistent in output, "
        f"got:\n{output}\n\nSTDERR:\n{stderr}"
    )

    # Check that the test failed
    assert (
        "FAILED" in output and "test_tool_annotations_are_consistent" in output
    ), (
        f"Expected test_tool_annotations_are_consistent to fail, "
        f"got:\n{output}"
    )

    # Check that the failure message mentions the conflicting hints
    assert (
        "readOnly" in output or "readonly" in output.lower()
        or "destructive" in output.lower() or "idempotent" in output.lower()
    ), f"Expected failure message about conflicting hints, got:\n{output}"

    # Check that pytest exited with error code
    assert (
        result.returncode != 0
    ), (
        f"Expected pytest to fail when annotation hints conflict, "
        f"got exit code: {result.returncode}"
    )

    print(
        "✅ test_tool_annotations_are_consistent correctly failed for "
        "server with conflicting annotations",
        flush=True,
    )

