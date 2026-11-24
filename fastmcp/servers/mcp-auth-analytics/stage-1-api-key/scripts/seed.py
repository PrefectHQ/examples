"""Builds the synthetic analytics warehouse. Fixed seed, so numbers repeat.

uv run python scripts/seed.py                # data/analytics.duckdb
uv run python scripts/seed.py --motherduck   # loads MotherDuck instead
"""

import argparse
import csv
import random
import sys
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from analytics_mcp import db  # noqa: E402

N_ACCOUNTS, USERS_PER_ACCOUNT, N_EVENTS, N_INVOICES = 500, 10, 200_000, 6_000
START = date(2025, 1, 1)
PLANS = [("free", 0), ("pro", 49), ("team", 199), ("enterprise", 999)]
REGIONS = ["NA", "EU", "APAC"]
EVENTS = [
    "login",
    "query_run",
    "dashboard_view",
    "export",
    "invite_sent",
    "alert_created",
]
FIRST = [
    "Ada",
    "Grace",
    "Linus",
    "Margaret",
    "Alan",
    "Edsger",
    "Barbara",
    "Ken",
    "Dennis",
    "Radia",
]
LAST = ["Example", "Sample", "Demo", "Placeholder", "Testcase"]
SCHEMA = """
CREATE TABLE accounts (account_id INTEGER PRIMARY KEY, company_name VARCHAR, plan VARCHAR,
                       region VARCHAR, signup_date DATE);
CREATE TABLE users (user_id INTEGER PRIMARY KEY, account_id INTEGER, email VARCHAR,
                    full_name VARCHAR, created_at TIMESTAMP);
CREATE TABLE events (event_id BIGINT PRIMARY KEY, user_id INTEGER, event_name VARCHAR,
                     occurred_at TIMESTAMP, properties JSON);
CREATE TABLE invoices (invoice_id INTEGER PRIMARY KEY, account_id INTEGER, amount_usd DECIMAL(10,2),
                       issued_at DATE, status VARCHAR);
"""


def generate(out: Path):
    rng = random.Random(42)
    rows = {"accounts": [], "users": [], "events": [], "invoices": []}
    plan_of = {}
    for a in range(1, N_ACCOUNTS + 1):
        plan = rng.choices(PLANS, weights=[40, 30, 20, 10])[0]
        plan_of[a] = plan
        rows["accounts"].append(
            [
                a,
                f"Example Co {a}",
                plan[0],
                rng.choice(REGIONS),
                START + timedelta(days=rng.randrange(0, 300)),
            ]
        )
    signup = {r[0]: r[4] for r in rows["accounts"]}
    uid = 0
    for a in range(1, N_ACCOUNTS + 1):
        for _ in range(USERS_PER_ACCOUNT):
            uid += 1
            created = datetime.combine(signup[a], datetime.min.time()) + timedelta(
                days=rng.randrange(0, 60), seconds=rng.randrange(86400)
            )
            created = min(created, datetime(2025, 12, 31))
            name = f"{rng.choice(FIRST)} {rng.choice(LAST)}"
            rows["users"].append([uid, a, f"user{uid}@example.com", name, created])
    users = rows["users"]
    for e in range(1, N_EVENTS + 1):
        u = users[rng.randrange(len(users))]
        when = u[4] + timedelta(seconds=rng.randrange(0, 200 * 86400))
        when = min(when, datetime(2025, 12, 31, 23, 59, 59))
        name = rng.choices(EVENTS, weights=[40, 25, 20, 5, 5, 5])[0]
        rows["events"].append([e, u[0], name, when, '{"source": "web"}'])
    for i in range(1, N_INVOICES + 1):
        a = rng.randrange(1, N_ACCOUNTS + 1)
        price = plan_of[a][1]
        if price == 0:
            price = 9
        month = START + timedelta(days=30 * rng.randrange(0, 12))
        rows["invoices"].append(
            [i, a, price, month, rng.choices(["paid", "open", "void"], [85, 10, 5])[0]]
        )
    for table, data in rows.items():
        with open(out / f"{table}.csv", "w", newline="") as f:
            csv.writer(f).writerows(data)


def load(con, folder: Path):
    for stmt in SCHEMA.split(";"):
        if stmt.strip():
            con.execute(stmt)
    for t in ("accounts", "users", "events", "invoices"):
        con.execute(
            f"COPY {t} FROM '{folder / (t + '.csv')}' (FORMAT csv, HEADER false)"
        )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--motherduck", action="store_true")
    args = p.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        generate(Path(tmp))
        if args.motherduck:
            con = db.motherduck_seed_connection()
            for t in ("events", "invoices", "users", "accounts"):
                con.execute(f"DROP TABLE IF EXISTS {t}")
        else:
            path = db.LOCAL_PATH
            path.parent.mkdir(exist_ok=True)
            path.unlink(missing_ok=True)
            con = db.duckdb.connect(str(path))
        load(con, Path(tmp))
        counts = {
            t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("accounts", "users", "events", "invoices")
        }
        con.close()
    print("seeded:", counts)


if __name__ == "__main__":
    main()
