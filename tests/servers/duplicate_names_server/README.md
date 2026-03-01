# Duplicate Names Server

A minimal MCP test server that returns tools with duplicate name fields.

Used to verify that the `test_tools_have_unique_names` check correctly detects
and fails when a server exposes multiple tools sharing the same name.
