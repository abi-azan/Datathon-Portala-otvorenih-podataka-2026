"""python -m fiskalna_mcp [--api <URL or folder>] [--timeout S]: the MCP server over stdio."""

from __future__ import annotations

import argparse
import sys

from .api import DEFAULT_API, DEFAULT_TIMEOUT
from .server import create_server


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="python -m fiskalna_mcp",
                                 description="MCP server Fiskalna karta (samo čitanje, stdio).")
    ap.add_argument("--api", default=DEFAULT_API,
                    help=f"URL ili mapa statičnog API-ja (zadano {DEFAULT_API}; za rad bez mreže web/public/api/v1)")
    ap.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="vremensko ograničenje upita, s")
    args = ap.parse_args(argv)
    # stdout carries the protocol; anything else goes to stderr
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    create_server(args.api, timeout=args.timeout).run("stdio")


if __name__ == "__main__":
    main()
