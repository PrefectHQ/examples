# Stage 1: one shared API key

Part of the [MCP authentication example](../README.md): one FastMCP server over a synthetic analytics warehouse, secured in three stages. Each stage folder is a complete, runnable copy of the server.

| Folder | What changes | What it shows |
| --- | --- | --- |
| **[`stage-1-api-key/`](../stage-1-api-key/)** | One shared key (`StaticTokenVerifier`) | Every caller is the same identity, and everyone can `delete_user` |
| [`stage-2-oauth/`](../stage-2-oauth/) | Keycloak + `KeycloakAuthProvider` | Real per-user and per-service identity, still no limits |
| [`stage-3-authz/`](../stage-3-authz/) | Roles, scope, tool visibility, `audit.log` | Each caller sees a different server |

`tools.py` is identical in every stage, so `diff -ru stage-1-api-key/src stage-3-authz/src` (run from the example folder) shows only the security change.

## Run it

Needs [uv](https://docs.astral.sh/uv/). No Docker for this stage.

```bash
make stage1
make test
```

`make stage1` reseeds the local DuckDB data (`delete_user` mutates it), starts the server with the key `demo-shared-key`, runs `demos/stage1.py`, and stops the server.

## What the demo shows

1. **No key:** the server answers `401` with a `Bearer` challenge. It is not open.
2. **Alice and Bob use the same key:** `whoami` returns the same answer for both. The server sees one caller, `shared-api-key`.
3. **What the key can do:** all eight tools are visible, including `delete_user`, and the delete goes through.
4. **The log:** every line has the same `client_id`, so nothing records who deleted user 42.

A shared key proves the caller had the key. It doesn't say who they are, and you can't revoke one person without changing it for everyone.

## Where to look

- `src/analytics_mcp/auth.py`: the whole stage, one `StaticTokenVerifier` mapping a key to a single identity. FastMCP marks it development-only, but a JWT minted for a shared key has the same problem.
- `src/analytics_mcp/tools.py`: the eight tools, with no auth logic.
- `src/analytics_mcp/audit.py`: one JSON line per tool call.

## Next

```bash
diff -ru src ../stage-2-oauth/src
cd ../stage-2-oauth
```

Stage 2 replaces the key with OAuth through Keycloak, so every caller gets a real identity.

Not included: FastMCP Gateway, TLS, secrets management, or anything production-grade.
