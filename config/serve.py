#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from livereload import Server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve the docs directory with livereload")
    parser.add_argument(
        "root",
        nargs="?",
        default=Path(__file__).resolve().parent.parent / "docs",
        help="Directory to serve (defaults to the docs directory)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", "8000")),
        help="Port to listen on (defaults to PORT env or 8000)",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "127.0.0.1"),
        help="Host interface to bind to (defaults to HOST env or 127.0.0.1)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        raise SystemExit(f"Serve root {root} is not a directory")

    server = Server()
    server.watch(str(root / "*.html"))
    server.watch(str(root / "statics" / "**" / "*.*"), delay=0.1)
    server.watch(str(root / "**" / "*.xml"), delay=0.5)
    server.serve(host=args.host, port=args.port, root=str(root))


if __name__ == "__main__":
    main()
