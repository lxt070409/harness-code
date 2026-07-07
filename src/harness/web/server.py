"""Server launcher for Harness Web UI."""

import argparse
import uvicorn


def run_server(args: argparse.Namespace | None = None):
    port = args.port if args and args.port else 8080
    host = args.host if args and args.host else "127.0.0.1"

    print(f"🌐 Harness Web UI starting at http://{host}:{port}")
    uvicorn.run("harness.web:app", host=host, port=port, log_level="info")
