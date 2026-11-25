"""Stage 2 logic that needs no Keycloak: provider wiring and token validation."""

from analytics_mcp.auth import REALM_URL, SERVER_URL, build_auth

from fastmcp.server.auth.providers.jwt import JWTVerifier


def test_provider_is_bound_to_this_server_and_realm():
    auth = build_auth()
    assert auth.realm_url == REALM_URL
    verifier = auth.token_verifier
    assert isinstance(verifier, JWTVerifier)
    assert verifier.audience == SERVER_URL
    assert verifier.issuer == REALM_URL
