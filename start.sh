#!/bin/bash
# Unified entrypoint for Railway services
# Set SERVICE_TYPE=mcp for the MCP service, leave empty for API

if [ "$SERVICE_TYPE" = "mcp" ]; then
    echo "Starting TPA Curriculum MCP Server"
    # Ensure mcp is installed (belt-and-suspenders for build cache issues)
    /app/venv/bin/pip install mcp>=1.0.0 --quiet 2>/dev/null || true
    exec /app/venv/bin/python mcp_server.py
else
    echo "Starting TPA API Server"
    exec /app/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
fi
