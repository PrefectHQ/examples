"""Stage 3 demo: same identity provider, now each caller sees a different server."""

import asyncio
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _run import ROOT, URL, heading, say, server  # noqa: E402
from login import as_user, bot_auth  # noqa: E402

from fastmcp import Client  # noqa: E402

INTERACTIVE = "--interactive" in sys.argv
AUDIT = ROOT / "audit.log"


async def main():
    heading("1. tools/list as alice, fran and adam")
    lists = {}
    for user in ("alice", "fran", "adam"):
        async with as_user(URL, user, INTERACTIVE) as c:
            lists[user] = [t.name for t in await c.list_tools()]
    every = sorted(set().union(*lists.values()))
    say(f"   {'tool':<20}" + "".join(f"{u:<8}" for u in lists))
    for tool in every:
        say(
            f"   {tool:<20}"
            + "".join(f"{('yes' if tool in lists[u] else '-'):<8}" for u in lists)
        )

    heading("2. alice calls get_revenue directly")
    async with as_user(URL, "alice", INTERACTIVE) as c:
        try:
            await c.call_tool(
                "get_revenue", {"start_month": "2025-01-01", "end_month": "2025-06-30"}
            )
        except Exception as exc:
            say(f"   denied: {exc}")

    heading("3. adam deletes a user")
    async with as_user(URL, "adam", INTERACTIVE) as c:
        say(f"   {(await c.call_tool('delete_user', {'user_id': 44})).data}")

    heading("4. nightly-report-bot reads a metric")
    async with Client(URL, auth=bot_auth(URL)) as c:
        rows = (
            await c.call_tool(
                "get_metric",
                {"metric": "dau", "start": "2025-03-01", "end": "2025-03-03"},
            )
        ).data
        say(f"   {len(rows)} rows")

    heading("5. audit.log summary")
    entries = [json.loads(line) for line in AUDIT.read_text().splitlines()]
    calls = Counter(e["username"] for e in entries)
    denials = Counter(e["tool"] for e in entries if e["outcome"] == "denied")
    say(
        "   calls per user:    "
        + ", ".join(f"{u}={n}" for u, n in sorted(calls.items()))
    )
    say(
        "   denials per tool:  "
        + (", ".join(f"{t}={n}" for t, n in denials.items()) or "none")
    )
    say("   last entries:")
    for e in entries[-3:]:
        say(f"     {json.dumps(e)}")

    if os.getenv("ANALYTICS_DB") == "motherduck":
        heading("6. Second layer: the database token, not FastMCP, blocks the write")
        sys.path.insert(0, str(ROOT / "src"))
        from analytics_mcp import db

        with db.read_connection() as con:
            say(
                f"   read token can read: {con.execute('SELECT count(*) FROM users').fetchone()[0]} users"
            )
            try:
                con.execute("DELETE FROM events WHERE user_id = 1")
                say("   UNEXPECTED: the read token wrote")
            except Exception as exc:
                say(f"   write attempt failed: {type(exc).__name__}: {str(exc)[:200]}")


if __name__ == "__main__":
    AUDIT.unlink(missing_ok=True)
    with server({"AUDIT_LOG": str(AUDIT)}):
        asyncio.run(main())
