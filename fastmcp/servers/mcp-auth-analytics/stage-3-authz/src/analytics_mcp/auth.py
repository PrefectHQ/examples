"""Stage 3: authentication (stage 2) plus authorization.

Keycloak says who the caller is. Everything below decides what that caller may do.
"""

import os

from fastmcp.exceptions import AuthorizationError
from fastmcp.server.auth import AuthCheck, AuthContext, require_roles, require_scopes
from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider
from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import AuthMiddleware, Middleware

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
REALM_URL = os.getenv(
    "KEYCLOAK_REALM_URL", "http://localhost:8080/realms/analytics-demo"
)
SERVER_SCOPE = "analytics:read"


def build_auth() -> KeycloakAuthProvider:
    # The 401 challenge advertises the required scopes, and clients request exactly
    # those. analytics:read also carries the roles and audience claims in our realm.
    return KeycloakAuthProvider(
        realm_url=REALM_URL,
        base_url=SERVER_URL,
        audience=SERVER_URL,
        required_scopes=["openid", SERVER_SCOPE],
    )


def keycloak_roles(claims: dict) -> list[str]:
    """Keycloak puts realm roles at realm_access.roles."""
    return claims["realm_access"]["roles"]


def has_role(*roles: str) -> AuthCheck:
    """Caller holds at least ONE of these roles. (require_roles alone means ALL of them.)"""
    checks = [require_roles(r, extract=keycloak_roles) for r in roles]

    def check(ctx: AuthContext) -> bool:
        return any(c(ctx) for c in checks)

    return check


# Per-tool checks, matching the tools table in the spec. A tool whose check fails
# is hidden from tools/list, and calling it by name fails as if it did not exist.
TOOL_AUTH: dict[str, AuthCheck | None] = {
    "list_metrics": None,
    "whoami": None,
    "get_metric": has_role("analyst", "finance", "admin"),
    "top_events": has_role("analyst", "finance", "admin"),
    "get_revenue": has_role("finance", "admin"),
    "lookup_account": has_role("admin"),
    "export_user_events": has_role("admin"),
    "delete_user": has_role("admin"),
}

# Layer 1: every component on the server needs this scope on the token.
server_wide = AuthMiddleware(auth=require_scopes(SERVER_SCOPE))


class EURegionGuard(Middleware):
    """A check a plain role list cannot express: it depends on the call's arguments.

    get_metric(region="EU") also needs the `eu-data` role.
    """

    async def on_call_tool(self, context, call_next):
        args = context.message.arguments or {}
        if context.message.name == "get_metric" and args.get("region") == "EU":
            token = get_access_token()
            roles = (
                (token.claims.get("realm_access") or {}).get("roles", [])
                if token
                else []
            )
            if "eu-data" not in roles:
                raise AuthorizationError("EU data requires the eu-data role")
        return await call_next(context)
