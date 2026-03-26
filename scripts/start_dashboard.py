#!/usr/bin/env python3
"""
Start the Job Intelligence Dashboard server.

Usage:
    python scripts/start_dashboard.py [--host HOST] [--port PORT]

Defaults to http://0.0.0.0:8080
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).resolve().parent.parent)
sys.path.insert(0, project_root)

from src.dashboard.app import start_dashboard


def main():
    parser = argparse.ArgumentParser(description="Job Intelligence Dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8888, help="Port to bind (default: 8888)")
    args = parser.parse_args()

    print("=" * 50)
    print("Job Intelligence Dashboard")
    print(f"Starting on http://{args.host}:{args.port}")
    print("=" * 50)

    start_dashboard(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
