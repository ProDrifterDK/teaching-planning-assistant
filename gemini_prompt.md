# Prompt for Gemini/Deep Research

I am trying to deploy a Python FastAPI application on Railway using Nixpacks. The application uses `weasyprint` for PDF generation.
I am encountering issues with missing shared libraries at runtime.

## Context
- **Platform:** Railway
- **Builder:** Nixpacks
- **Language:** Python 3.11
- **Key Dependency:** `weasyprint` (which uses `cffi` and `glib`/`pango`/`cairo`)

## Issues
1. Initially, I got `OSError: cannot load library 'libgobject-2.0-0': libgobject-2.0-0: cannot open shared object file: No such file or directory.`
2. I tried adding system packages to `nixPkgs` and then `nixLibs` in `nixpacks.toml`.
3. After adding `glib`, `pango`, `cairo`, etc. to `nixLibs`, I encountered a new error: `ImportError: libstdc++.so.6: cannot open shared object file: No such file or directory`.

## Current `nixpacks.toml`
```toml
[phases.setup]
nixPkgs = ["python311", "python311Packages.pip", "pkg-config"]
nixLibs = ["glib", "gobject-introspection", "cairo", "pango", "gdk-pixbuf", "harfbuzz", "libffi", "fontconfig", "stdenv.cc.cc.lib", "zlib"]

[phases.install]
cmds = [
    "python -m venv /app/venv",
    "/app/venv/bin/pip install --upgrade pip",
    "/app/venv/bin/pip install -r requirements.txt"
]

[start]
cmd = "/app/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port $PORT"
```

## Request
Please provide a robust `nixpacks.toml` configuration that correctly sets up the environment for `weasyprint` on Railway/Nixpacks.
Specifically:
1. How to ensure `libgobject-2.0-0` and other `weasyprint` dependencies are found by `cffi`?
2. How to resolve the `libstdc++.so.6` missing error?
3. Are there any specific environment variables (like `LD_LIBRARY_PATH`) I need to set manually, or should `nixLibs` handle it?
4. Is there a better way to define the dependencies (e.g., using a specific provider or overlay)?

Please analyze the Nixpacks behavior and provide a working configuration.
