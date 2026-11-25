# MCP authentication: API keys, OAuth and roles

Targets FastMCP 4.2.2, Keycloak 26.8.2 and Python 3.12+.

One [FastMCP](https://gofastmcp.com) server over a synthetic analytics warehouse (accounts, users, events, invoices), secured in three stages. It's the companion code for the article *MCP authentication: OAuth vs API keys, explained*.

| Folder | What changes | What it shows |
| --- | --- | --- |
| [`stage-1-api-key/`](stage-1-api-key/) | One shared key (`StaticTokenVerifier`) | Every caller is the same identity, and everyone can `delete_user` |
| [`stage-2-oauth/`](stage-2-oauth/) | Keycloak + `KeycloakAuthProvider` | Real per-user and per-service identity, still no limits |
| [`stage-3-authz/`](stage-3-authz/) | Roles, scope, tool visibility, `audit.log` | Each caller sees a different server |

Each stage folder is a complete, runnable copy of the server with its own README. `tools.py` is identical in every stage, so the security change is all that differs:

```bash
diff -ru stage-1-api-key/src stage-2-oauth/src
diff -ru stage-2-oauth/src stage-3-authz/src
```

## Run it

Needs [uv](https://docs.astral.sh/uv/) and, for stages 2 and 3, Docker. All three stages share this folder's `pyproject.toml` and `uv.lock`.

```bash
cd stage-1-api-key && make stage1 && cd ..
cd stage-2-oauth   && make up && make stage2 && cd ..
cd stage-3-authz   && make stage3 && make down    # Keycloak from `make up` still running
```

Each `make stageN` reseeds the local DuckDB data, starts the server, runs that stage's scripted demo, and stops the server. `make test` in any stage runs its tests without Keycloak.

Stage 3 also shows how to connect Claude Code, which signs in with a Client ID Metadata Document (CIMD), and an optional MotherDuck setup that adds a database-level permission layer.

The Keycloak users and secrets in the realm files are demo credentials for a local container. Don't reuse them anywhere.

Not included: FastMCP Gateway, TLS, secrets management, or anything production-grade.
