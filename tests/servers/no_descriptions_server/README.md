# No Descriptions Test Server

A simple MCP server with tools that are missing description fields, used for testing description validation.

## Features

- **tool_without_description**: A tool that intentionally lacks a description field to test validation

## Purpose

This server is used to test that the pytest-mcp-tools plugin correctly identifies and fails when tools are missing required description fields.

## Running Locally

```bash
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

## Running with Docker

```bash
docker build -t no-descriptions-server .
docker run -p 8000:8000 no-descriptions-server
```
