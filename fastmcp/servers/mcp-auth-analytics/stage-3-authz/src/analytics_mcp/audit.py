"""Structured audit log: one JSON object per line in audit.log."""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from fastmcp.exceptions import AuthorizationError, NotFoundError
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware

EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def redact(value):
    if isinstance(value, str):
        return EMAIL.sub("[email]", value)
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class AuditMiddleware(Middleware):
    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.getenv("AUDIT_LOG", "audit.log"))

    def _write(self, entry: dict) -> None:
        with self.path.open("a") as f:
            f.write(json.dumps(entry) + "\n")

    async def on_call_tool(self, context, call_next):
        token = get_access_token()
        claims = (token.claims or {}) if token else {}
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "sub": claims.get("sub"),
            "username": claims.get("preferred_username"),
            "roles": (claims.get("realm_access") or {}).get("roles", []),
            "tool": context.message.name,
            "arguments": redact(context.message.arguments or {}),
        }
        try:
            result = await call_next(context)
        except (AuthorizationError, NotFoundError) as exc:
            entry |= {"outcome": "denied", "reason": f"{type(exc).__name__}: {exc}"}
            self._write(entry)
            raise
        except Exception as exc:
            entry |= {"outcome": "error", "reason": f"{type(exc).__name__}: {exc}"}
            self._write(entry)
            raise
        entry |= {"outcome": "allowed", "reason": "ok"}
        self._write(entry)
        return result
