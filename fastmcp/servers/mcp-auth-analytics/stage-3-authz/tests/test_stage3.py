"""Stage 3 logic without Keycloak: mint tokens that look like Keycloak's."""

import json

import pytest
from analytics_mcp.audit import redact
from analytics_mcp.server import build_server

from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.exceptions import ToolError
from fastmcp.server.auth.providers.jwt import JWTVerifier, RSAKeyPair
from fastmcp.utilities.tests import run_server_async

ISSUER, AUD = "http://localhost:8080/realms/analytics-demo", "http://localhost:8000"
ALL = {
    "list_metrics",
    "whoami",
    "get_metric",
    "top_events",
    "get_revenue",
    "lookup_account",
    "export_user_events",
    "delete_user",
}
EXPECTED = {
    "alice": {"list_metrics", "whoami", "get_metric", "top_events"},
    "fran": {"list_metrics", "whoami", "get_metric", "top_events", "get_revenue"},
    "adam": ALL,
}
ROLES = {"alice": ["analyst"], "fran": ["finance"], "adam": ["admin", "eu-data"]}


@pytest.fixture(scope="module")
def keys():
    return RSAKeyPair.generate()


def token(keys, user, roles, scopes=("openid", "analytics:read")):
    return keys.create_token(
        subject=f"sub-{user}",
        issuer=ISSUER,
        audience=AUD,
        scopes=list(scopes),
        additional_claims={
            "preferred_username": user,
            "realm_access": {"roles": roles},
        },
    )


@pytest.fixture
async def url(keys, warehouse, tmp_path):
    verifier = JWTVerifier(
        public_key=keys.public_key,
        issuer=ISSUER,
        audience=AUD,
        required_scopes=["openid"],
    )
    server = build_server(auth=verifier, audit_path=tmp_path / "audit.log")
    async with run_server_async(server) as u:
        yield u


def audit(tmp_path):
    p = tmp_path / "audit.log"
    return [json.loads(line) for line in p.read_text().splitlines()]


@pytest.mark.parametrize("user", EXPECTED)
async def test_tools_list_differs_per_role(url, keys, user):
    async with Client(url, auth=BearerAuth(token(keys, user, ROLES[user]))) as c:
        assert {t.name for t in await c.list_tools()} == EXPECTED[user]


async def test_hidden_tool_is_denied_and_logged(url, keys, tmp_path):
    async with Client(url, auth=BearerAuth(token(keys, "alice", ROLES["alice"]))) as c:
        with pytest.raises(ToolError):
            await c.call_tool(
                "get_revenue", {"start_month": "2025-01-01", "end_month": "2025-06-30"}
            )
    last = audit(tmp_path)[-1]
    assert (last["username"], last["tool"], last["outcome"]) == (
        "alice",
        "get_revenue",
        "denied",
    )
    assert last["reason"]


async def test_admin_delete_lands_in_audit_log(url, keys, tmp_path):
    async with Client(url, auth=BearerAuth(token(keys, "adam", ROLES["adam"]))) as c:
        out = await c.call_tool("delete_user", {"user_id": 11})
    assert out.data["users_deleted"] == 1
    last = audit(tmp_path)[-1]
    assert (last["username"], last["tool"], last["outcome"]) == (
        "adam",
        "delete_user",
        "allowed",
    )
    assert last["sub"] == "sub-adam" and "admin" in last["roles"]


async def test_missing_server_scope_blocks_everything(url, keys):
    bad = token(keys, "alice", ["analyst"], scopes=("openid",))
    async with Client(url, auth=BearerAuth(bad)) as c:
        assert await c.list_tools() == []


async def test_eu_region_needs_eu_data_role(url, keys):
    args = {
        "metric": "signups",
        "start": "2025-03-01",
        "end": "2025-03-07",
        "region": "EU",
    }
    async with Client(url, auth=BearerAuth(token(keys, "alice", ROLES["alice"]))) as c:
        with pytest.raises(ToolError):
            await c.call_tool("get_metric", args)
    async with Client(url, auth=BearerAuth(token(keys, "adam", ROLES["adam"]))) as c:
        assert (await c.call_tool("get_metric", args)).data


async def test_service_account_identity_is_logged(url, keys, tmp_path):
    bot = token(keys, "service-account-nightly-report-bot", ["analyst"])
    async with Client(url, auth=BearerAuth(bot)) as c:
        await c.call_tool(
            "get_metric", {"metric": "dau", "start": "2025-03-01", "end": "2025-03-02"}
        )
    assert audit(tmp_path)[-1]["username"] == "service-account-nightly-report-bot"


def test_emails_are_redacted():
    assert redact({"q": "mail ada@example.com now", "n": [1, "b@x.io"]}) == {
        "q": "mail [email] now",
        "n": [1, "[email]"],
    }
