"""Read-only MCP server "Fiskalna karta" over the project's static API (PLAN §5).

The package is not called `mcp`, because that name would shadow the MCP Python SDK on import.
Run it with `python -m fiskalna_mcp [--api <URL or folder>]`; docs/mcp.md has the details.
"""

from .api import DEFAULT_API, PUBLIC_SITE, Api, ApiError
from .server import create_server

__all__ = ["Api", "ApiError", "DEFAULT_API", "PUBLIC_SITE", "create_server"]
