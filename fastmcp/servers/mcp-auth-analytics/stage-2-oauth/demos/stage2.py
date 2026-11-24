"""Stage 2 demo: OAuth gives every caller a real identity. It does not limit them."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _run import URL, heading, say, server  # noqa: E402
from login import as_user, bot_auth  # noqa: E402

from fastmcp import Client  # noqa: E402

INTERACTIVE = "--interactive" in sys.argv


async def identity(client):
    return (await client.call_tool("whoami")).data


async def main(log_path):
    for step, user in ((1, "alice"), (2, "adam")):
        heading(f"{step}. Log in as {user}")
        async with as_user(URL, user, INTERACTIVE) as c:
            say(f"   {json.dumps(await identity(c))}")

    heading("3. A non-human caller: nightly-report-bot (client credentials)")
    async with Client(URL, auth=bot_auth(URL)) as c:
        say(f"   {json.dumps(await identity(c))}")

    heading("4. Authenticated is not authorized: alice can still delete a user")
    async with as_user(URL, "alice", INTERACTIVE) as c:
        say(f"   visible tools: {len(await c.list_tools())} of 8")
        say(
            f"   delete_user(43): {(await c.call_tool('delete_user', {'user_id': 43})).data}"
        )

    heading("Log now names the caller")
    for line in Path(log_path).read_text().splitlines():
        if line.startswith("{"):
            say(f"   {line}")


if __name__ == "__main__":
    with server() as log:
        asyncio.run(main(log))
