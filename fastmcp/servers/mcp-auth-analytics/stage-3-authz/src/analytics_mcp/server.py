"""FastMCP app. Auth is wired here, per stage. Run: python -m analytics_mcp.server"""

import os

from fastmcp import FastMCP

from . import tools
from .audit import AuditMiddleware
from .auth import TOOL_AUTH, EURegionGuard, build_auth, server_wide

PORT = int(os.getenv("PORT", "8000"))

TOOLS = (
    tools.list_metrics,
    tools.get_metric,
    tools.top_events,
    tools.get_revenue,
    tools.lookup_account,
    tools.export_user_events,
    tools.delete_user,
    tools.whoami,
)


def build_server(auth=None, audit_path=None) -> FastMCP:
    # Order matters: audit sees every call, including the denied ones.
    mcp = FastMCP(
        "analytics",
        auth=auth or build_auth(),
        middleware=[AuditMiddleware(audit_path), server_wide, EURegionGuard()],
    )
    for fn in TOOLS:
        mcp.tool(fn, auth=TOOL_AUTH[fn.__name__])
    return mcp


if __name__ == "__main__":
    build_server().run(transport="http", host="127.0.0.1", port=PORT)
