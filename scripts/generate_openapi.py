#!/usr/bin/env python
"""Generate OpenAPI specification from FastAPI app"""
import json
import sys
import os

# Add current directory to path so we can import api
sys.path.insert(0, '.')

from api.main import app

# Ensure output directory exists
os.makedirs('docs/api', exist_ok=True)

openapi_schema = app.openapi()

# Write to file
with open('docs/api/openapi.json', 'w') as f:
    json.dump(openapi_schema, f, indent=2)

print("OpenAPI spec generated: docs/api/openapi.json")