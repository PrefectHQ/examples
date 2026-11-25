import pytest
from analytics_mcp.auth import build_auth


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.setenv("ANALYTICS_API_KEY", "k")
    return build_auth()


async def test_wrong_key_rejected(verifier):
    assert await verifier.verify_token("nope") is None


async def test_every_caller_is_the_same_identity(verifier):
    alice = await verifier.verify_token("k")
    bob = await verifier.verify_token("k")
    assert alice.client_id == bob.client_id == "shared-api-key"
    assert alice.claims.get("sub") is None  # nothing to tell callers apart
