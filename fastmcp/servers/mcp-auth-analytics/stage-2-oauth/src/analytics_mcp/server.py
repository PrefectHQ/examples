"""FastMCP app. Auth is wired here, per stage. Run: python -m analytics_mcp.server"""

import os

from fastmcp import FastMCP

from . import tools
from .audit import AuditMiddleware
from .auth import build_auth

PORT = int(os.getenv("PORT", "8000"))


def build_server() -> FastMCP:
    mcp = FastMCP("analytics", auth=build_auth(), middleware=[AuditMiddleware()])
    for fn in (
        tools.list_metrics,
        tools.get_metric,
        tools.top_events,
        tools.get_revenue,
        tools.lookup_account,
        tools.export_user_events,
        tools.delete_user,
        tools.whoami,
    ):
        mcp.tool(fn)
    return mcp


if __name__ == "__main__":
    build_server().run(transport="http", host="127.0.0.1", port=PORT)
