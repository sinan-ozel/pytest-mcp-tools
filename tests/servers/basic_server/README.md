# Basic Test Server

A simple MCP server built with FastMCP for testing purposes.

## Features

- **stream_message**: A tool that streams a given message back to the client

## Running Locally

```bash
pip install -r requirements.txt
python server.py
```

## Running with Docker

```bash
docker build -t basic-test-server .
docker run -i basic-test-server
```

## Usage

The server exposes one tool:

- `stream_message(message: str) -> str`: Returns the message that was provided as input
