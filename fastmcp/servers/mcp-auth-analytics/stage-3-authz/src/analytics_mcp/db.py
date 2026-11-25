"""Backend switch: local DuckDB (default) or MotherDuck.

Two kinds of connection, so the database can enforce what the tools may do:

* ``read_connection()``  read-only. Used by every tool except ``delete_user``.
* ``write_connection()`` read/write. Used by ``delete_user`` and seeding only.

Local mode opens a short-lived connection per call and closes it, because DuckDB
refuses to hold a read-only and a read/write connection to the same file open
at once. MotherDuck mode uses a read scaling token for reads and a short-lived
read/write token for the one write path.
"""

import os
import threading
from contextlib import contextmanager
from pathlib import Path

import duckdb

LOCAL_PATH = Path(__file__).resolve().parents[2] / "data" / "analytics.duckdb"
MD_DB = "analytics_demo"
_lock = threading.Lock()


def backend() -> str:
    return os.getenv("ANALYTICS_DB", "local")


def _md_connect(token_var: str, role: str):
    token = os.environ[token_var]  # never from code or the connection string
    # DuckDB caches one instance per path and refuses a second config for it, so the
    # two tokens need two distinct paths. `session_hint` is a documented MotherDuck
    # parameter; here it only keeps the read and write connections apart.
    return duckdb.connect(
        f"md:{MD_DB}?attach_mode=single&session_hint={role}",
        config={"motherduck_token": token},
    )


def motherduck_seed_connection():
    # Seeding creates the database, so connect without naming it first.
    token = os.environ["MOTHERDUCK_RW_TOKEN"]
    con = duckdb.connect("md:", config={"motherduck_token": token})
    con.execute(f"CREATE DATABASE IF NOT EXISTS {MD_DB}")
    con.execute(f"USE {MD_DB}")
    return con


@contextmanager
def read_connection():
    with _lock:
        if backend() == "motherduck":
            con = _md_connect("MOTHERDUCK_READ_TOKEN", "read")
        else:
            con = duckdb.connect(str(LOCAL_PATH), read_only=True)
        try:
            yield con
        finally:
            con.close()


@contextmanager
def write_connection():
    with _lock:
        if backend() == "motherduck":
            con = _md_connect("MOTHERDUCK_RW_TOKEN", "write")
        else:
            con = duckdb.connect(str(LOCAL_PATH))
        try:
            yield con
        finally:
            con.close()
