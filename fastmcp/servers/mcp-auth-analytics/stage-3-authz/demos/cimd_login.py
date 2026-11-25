"""Sign in the way a CIMD client does: no registration, the client ID is a URL.

This uses Claude Code's published Client ID Metadata Document as the client ID,
so it checks the same Keycloak path Claude Code takes when you connect it with
.mcp.json. Keycloak fetches the document from claude.ai (needs internet), shows
its consent screen (accepted here by the scripted login), and issues a token
whose client_id is the URL. From stage 3 on, the role rules apply as usual.
"""

import asyncio
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _run import URL, heading, say, server  # noqa: E402
from login import _login  # noqa: E402

from fastmcp import Client  # noqa: E402
from fastmcp.client.auth import OAuth  # noqa: E402

CLIENT_ID_URL = "https://claude.ai/oauth/claude-code-client-metadata"


def cimd_auth(user: str) -> OAuth:
    auth = OAuth(client_metadata_url=CLIENT_ID_URL)

    async def redirect_handler(authorization_url: str) -> None:
        threading.Thread(
            target=_login, args=(authorization_url, user, user), daemon=True
        ).start()

    auth.redirect_handler = redirect_handler  # type: ignore[method-assign]
    return auth


async def main():
    for user in ("fran", "alice"):
        heading(f"{user} signs in with client ID {CLIENT_ID_URL}")
        async with Client(URL, auth=cimd_auth(user)) as c:
            me = (await c.call_tool("whoami")).data
            say(f"   client_id: {me['client_id']}")
            say(
                f"   roles:     {', '.join(r for r in me['roles'] if r != 'offline_access')}"
            )
            say(f"   tools:     {', '.join(t.name for t in await c.list_tools())}")


if __name__ == "__main__":
    with server():
        asyncio.run(asyncio.wait_for(main(), 120))
