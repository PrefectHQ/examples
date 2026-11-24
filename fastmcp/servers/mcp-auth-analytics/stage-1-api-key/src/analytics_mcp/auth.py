"""Stage 1: one shared API key. Everyone who has it is the same caller."""

import os

from fastmcp.server.auth.providers.jwt import StaticTokenVerifier


def build_auth() -> StaticTokenVerifier:
    # StaticTokenVerifier is development-only: the key sits in plain text and
    # there is no expiry, rotation, or per-caller identity. That is the point
    # of stage 1.
    key = os.environ["ANALYTICS_API_KEY"]
    return StaticTokenVerifier(
        tokens={key: {"client_id": "shared-api-key", "scopes": []}}
    )
