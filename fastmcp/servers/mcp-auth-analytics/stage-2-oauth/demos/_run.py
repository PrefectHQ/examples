"""Starts the server as a subprocess for a demo and tears it down after."""

import os
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "http://localhost:8000/mcp"


def say(text=""):
    print(text, flush=True)


def heading(text):
    say(f"\n== {text}")


@contextmanager
def server(env=None):
    """Yield the path of the file holding the server's stdout."""
    log = tempfile.NamedTemporaryFile("w+", suffix=".log", delete=False)
    proc = subprocess.Popen(
        [sys.executable, "-m", "analytics_mcp.server"],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src"), **(env or {})},
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", 8000)) == 0:
                    break
            if proc.poll() is not None:
                raise RuntimeError(Path(log.name).read_text())
            time.sleep(0.1)
        yield log.name
    finally:
        proc.terminate()
        proc.wait(timeout=10)
