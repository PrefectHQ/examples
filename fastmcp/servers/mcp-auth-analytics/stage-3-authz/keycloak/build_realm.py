"""Regenerates realm-export.json. Run: uv run python keycloak/build_realm.py

Kept in the repo so the realm is reviewable as code. The JSON it writes is what
Keycloak imports on startup.
"""

import json
from pathlib import Path

SERVER_URL = "http://localhost:8000"


def mapper(name, kind, **config):
    return {
        "name": name,
        "protocol": "openid-connect",
        "protocolMapper": kind,
        "consentRequired": False,
        "config": {
            k: str(v).lower() if isinstance(v, bool) else v for k, v in config.items()
        },
    }


def scope(name, mappers=(), in_token_scope=True):
    return {
        "name": name,
        "protocol": "openid-connect",
        "attributes": {
            "include.in.token.scope": str(in_token_scope).lower(),
            "display.on.consent.screen": "false",
        },
        "protocolMappers": list(mappers),
    }


tok = dict(**{"id.token.claim": True, "access.token.claim": True})

client_scopes = [
    scope("openid", [mapper("sub", "oidc-sub-mapper", **tok)]),
    scope(
        "profile",
        [
            mapper(
                "username",
                "oidc-usermodel-attribute-mapper",
                **{
                    "user.attribute": "username",
                    "claim.name": "preferred_username",
                    "jsonType.label": "String",
                    "userinfo.token.claim": True,
                },
                **tok,
            )
        ],
    ),
    scope(
        "email",
        [
            mapper(
                "email",
                "oidc-usermodel-attribute-mapper",
                **{
                    "user.attribute": "email",
                    "claim.name": "email",
                    "jsonType.label": "String",
                    "userinfo.token.claim": True,
                },
                **tok,
            )
        ],
    ),
    # The one scope the server asks clients to request (see auth.py). Requesting it
    # also yields the two claims the server depends on, because Keycloak's dynamic
    # client registration makes requested scopes optional rather than default:
    #   realm_access.roles  realm roles, read by the stage 3 checks
    #   preferred_username  who is calling, for whoami and the logs
    #   aud                 this server's URL (the MCP spec requires audience-bound tokens)
    scope(
        "analytics:read",
        [
            mapper(
                "realm roles",
                "oidc-usermodel-realm-role-mapper",
                **{
                    "claim.name": "realm_access.roles",
                    "multivalued": True,
                    "jsonType.label": "String",
                    "userinfo.token.claim": False,
                },
                **{"id.token.claim": False, "access.token.claim": True},
            ),
            mapper(
                "username",
                "oidc-usermodel-attribute-mapper",
                **{
                    "user.attribute": "username",
                    "claim.name": "preferred_username",
                    "jsonType.label": "String",
                },
                **{"id.token.claim": False, "access.token.claim": True},
            ),
            mapper(
                "analytics-server-audience",
                "oidc-audience-mapper",
                **{
                    "included.custom.audience": SERVER_URL,
                    "access.token.claim": True,
                    "id.token.claim": False,
                },
            ),
        ],
    ),
]

default_scopes = ["openid", "profile", "email", "analytics:read"]


def user(name, role, extra_roles=()):
    return {
        "username": name,
        "email": f"{name}@example.com",
        "firstName": name.capitalize(),
        "lastName": "Demo",
        "enabled": True,
        "emailVerified": True,
        "credentials": [{"type": "password", "value": name, "temporary": False}],
        "realmRoles": [role, *extra_roles, "offline_access"],
    }


realm = {
    "realm": "analytics-demo",
    "displayName": "Analytics demo",
    "enabled": True,
    "registrationAllowed": False,
    "defaultDefaultClientScopes": default_scopes,
    "defaultOptionalClientScopes": [],
    "roles": {
        "realm": [{"name": n} for n in ("analyst", "finance", "admin", "eu-data")]
    },
    "clientScopes": client_scopes,
    # Put the roles on the scope, not on each client. Clients that register with a
    # Client ID Metadata Document get fullScopeAllowed=false, so without this they
    # would receive no realm roles. DCR clients get them either way.
    "scopeMappings": [
        {
            "clientScope": "analytics:read",
            "roles": ["analyst", "finance", "admin", "eu-data"],
        },
    ],
    "clients": [
        {
            "clientId": "nightly-report-bot",
            "name": "Nightly report bot",
            "description": "Non-human caller using the client credentials grant",
            "enabled": True,
            "publicClient": False,
            "secret": "nightly-report-bot-secret",
            "standardFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "serviceAccountsEnabled": True,
            "clientAuthenticatorType": "client-secret",
            "defaultClientScopes": default_scopes,
        }
    ],
    "users": [
        user("alice", "analyst"),
        user("fran", "finance"),
        user("adam", "admin", ["eu-data"]),
        {
            "username": "service-account-nightly-report-bot",
            "enabled": True,
            "serviceAccountClientId": "nightly-report-bot",
            "realmRoles": ["analyst"],
        },
    ],
    # CIMD (experimental in Keycloak, needs --features=cimd): a client whose ID is
    # an https URL on a trusted domain is accepted without registering first.
    # Keycloak fetches the document at that URL to learn the client's name and
    # redirect URIs. Claude Code's ID is https://claude.ai/oauth/claude-code-client-metadata
    # and it redirects to localhost, so both domains are trusted. Other clients
    # (no https URL ID) still fall back to dynamic registration below.
    "clientProfiles": {
        "profiles": [
            {
                "name": "mcp-cimd",
                "description": "MCP clients identified by a Client ID Metadata Document",
                "executors": [
                    {
                        "executor": "client-id-metadata-document",
                        "configuration": {
                            "cimd-allow-http-scheme": "false",
                            "cimd-allow-permitted-domains": [
                                "claude.ai",
                                "localhost",
                                "127.0.0.1",
                            ],
                            "cimd-restrict-same-domain": "false",
                            "only-allow-confidential-client": "false",
                        },
                    }
                ],
            }
        ]
    },
    "clientPolicies": {
        "policies": [
            {
                "name": "mcp-cimd",
                "description": "Send https client IDs on trusted domains to the CIMD profile",
                "enabled": True,
                "conditions": [
                    {
                        "condition": "client-id-uri",
                        "configuration": {
                            "client-id-uri-scheme": ["https"],
                            "client-id-uri-allow-permitted-domains": ["claude.ai"],
                        },
                    }
                ],
                "profiles": ["mcp-cimd"],
            }
        ]
    },
    "components": {
        "org.keycloak.services.clientregistration.policy.ClientRegistrationPolicy": [
            {
                "name": "Trusted Hosts",
                "providerId": "trusted-hosts",
                "subType": "anonymous",
                "subComponents": {},
                "config": {
                    "host-sending-registration-request-must-match": ["false"],
                    "trusted-hosts": ["localhost"],
                    "client-uris-must-match": ["true"],
                },
            }
        ]
    },
}

out = Path(__file__).with_name("realm-export.json")
out.write_text(json.dumps(realm, indent=2) + "\n")
print(f"wrote {out}")
