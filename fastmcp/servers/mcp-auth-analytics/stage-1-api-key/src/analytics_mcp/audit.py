"""Tool-call log. Stage 1: JSON lines on stdout. (Stage 3 replaces this with audit.log.)"""

import json
from datetime import datetime, timezone

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware


class AuditMiddleware(Middleware):
    async def on_call_tool(self, context, call_next):
        token = get_access_token()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "tool": context.message.name,
            "client_id": token.client_id if token else None,
            "arguments": context.message.arguments or {},
        }
        try:
            result = await call_next(context)
        except Exception:
            entry["success"] = False
            print(json.dumps(entry), flush=True)
            raise
        entry["success"] = True
        print(json.dumps(entry), flush=True)
        return result
