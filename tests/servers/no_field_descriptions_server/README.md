# No Field Descriptions Test Server

A simple MCP server with a tool whose `inputSchema` properties are missing `description` fields, used for testing per-field description validation.

## Features

- **process_data**: A tool with `inputSchema` properties that intentionally omit `description` fields to test field-level description validation

## Purpose

This server is used to test that the pytest-mcp-tools plugin correctly identifies and fails when `inputSchema` property fields are missing `description` fields.

## Running Locally

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Running with Docker

```bash
docker build -t no-field-descriptions-server .
docker run -p 8000:8000 no-field-descriptions-server
```
