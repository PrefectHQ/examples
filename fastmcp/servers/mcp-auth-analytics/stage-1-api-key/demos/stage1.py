"""Stage 1 demo: what a shared API key cannot tell you."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import httpx  # noqa: E402
from _run import URL, heading, say, server  # noqa: E402

from fastmcp import Client  # noqa: E402
from fastmcp.client.auth import BearerAuth  # noqa: E402

KEY = "demo-shared-key"


async def main(log_path):
    heading("1. No key")
    r = httpx.post(
        URL,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        headers={"accept": "application/json, text/event-stream"},
    )
    say(f"   HTTP {r.status_code} {r.headers.get('www-authenticate', '')[:70]}")

    heading("2. Alice and Bob use the same key")
    for who in ("Alice", "Bob"):
        async with Client(URL, auth=BearerAuth(KEY)) as c:
            who_am_i = (await c.call_tool("whoami")).data
            say(f"   {who}: {json.dumps(who_am_i)}")

    heading("3. The shared key can call delete_user")
    async with Client(URL, auth=BearerAuth(KEY)) as c:
        tools = [t.name for t in await c.list_tools()]
        say(f"   visible tools: {', '.join(tools)}")
        say(
            f"   delete_user(42): {(await c.call_tool('delete_user', {'user_id': 42})).data}"
        )

    heading("4. The log cannot tell them apart")
    for line in Path(log_path).read_text().splitlines():
        if line.startswith("{"):
            say(f"   {line}")


if __name__ == "__main__":
    with server({"ANALYTICS_API_KEY": KEY}) as log:
        asyncio.run(main(log))
