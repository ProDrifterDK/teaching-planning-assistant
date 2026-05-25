#!/bin/bash
# Unified entrypoint for Railway services

if [ "$SERVICE_TYPE" = "mcp" ]; then
    echo "=== MCP: Installing mcp package ==="
    /app/venv/bin/pip install 'mcp>=1.26.0'
    echo "=== MCP: Starting server ==="
    exec /app/venv/bin/python mcp_server.py
else
    echo "=== API: Starting server ==="
    exec /app/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
