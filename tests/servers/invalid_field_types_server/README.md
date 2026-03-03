# Invalid Field Types Test Server

A simple MCP server with a tool whose `inputSchema` properties have missing or invalid `type` fields, used for testing per-field type validation.

## Features

- **transform_data**: A tool with `inputSchema` properties that intentionally have an invalid type (`"text"` instead of `"string"`) and a missing `type` field, to test field-level type validation

## Purpose

This server is used to test that the pytest-mcp-tools plugin correctly identifies and fails when `inputSchema` property fields have missing or non-standard `type` values.

## Running Locally

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Running with Docker

```bash
docker build -t invalid-field-types-server .
docker run -p 8000:8000 invalid-field-types-server
```
