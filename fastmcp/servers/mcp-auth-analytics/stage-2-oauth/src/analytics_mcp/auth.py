"""Stage 2: OAuth. Keycloak authenticates people; this server only validates tokens."""

import os

from fastmcp.server.auth.providers.keycloak import KeycloakAuthProvider

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
REALM_URL = os.getenv(
    "KEYCLOAK_REALM_URL", "http://localhost:8080/realms/analytics-demo"
)
SERVER_SCOPE = "analytics:read"


def build_auth() -> KeycloakAuthProvider:
    # The 401 challenge advertises the required scopes and clients request exactly
    # those. In our realm analytics:read also carries preferred_username and the
    # audience claim, because Keycloak's dynamic client registration makes
    # requested scopes optional rather than default.
    return KeycloakAuthProvider(
        realm_url=REALM_URL,
        base_url=SERVER_URL,
        # The spec requires tokens bound to this server: reject any other audience.
        audience=SERVER_URL,
        required_scopes=["openid", SERVER_SCOPE],
    )
