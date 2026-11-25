"""Run examples from the product folders, each in its own environment.

Examples are found with ``internal.catalog.discover``, so anything the runner
sees also follows the example contract (``internal/example-contract.md``).

Usage::

    python -m internal.runner run hello weather           # by slug
    python -m internal.runner run --changed-since origin/main
    python -m internal.runner run --all --product prefect --upgrade prefect
    python -m internal.runner run --all --dry-run         # list, don't run
    python -m internal.runner open-issues results.json    # after a failed run

How each example runs:

- A folder example runs ``uv run --project <folder> --locked python <entrypoint>``
  from inside the folder, so it uses its own ``uv.lock``.
- A single-file example runs in a throwaway environment built from its
  ``targets`` and ``dependencies``:
  ``uv run --isolated --no-project --with <target> ... python <file>``.
  If it sets ``cmd``, that command runs instead of ``python <file>``.
- ``test: import-only`` imports the entrypoint without running its
  ``if __name__ == "__main__"`` block. ``test: skip`` is never run.
- Examples whose ``requires_secrets`` aren't all set in the environment are
  skipped, not failed.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from .catalog import PRODUCTS, REPO_ROOT, Example, discover

# Changes to these files can change how every example runs, so a PR that touches
# them runs every maintained example.
RUNNER_FILES = (
    "internal/runner.py",
    "internal/catalog.py",
    ".github/workflows/pr.yml",
)

# Import a file as a module without running its ``__main__`` block.
# Like ``python <file>``, put the file's own folder first on sys.path so it can
# import the modules next to it.
IMPORT_ONLY = (
    "import os, runpy, sys; path = sys.argv[1]; sys.argv = sys.argv[1:]; "
    "sys.path.insert(0, os.path.dirname(os.path.abspath(path))); "
    "runpy.run_path(path, run_name='__example__')"
)

# After a timeout, how long the example gets to exit on SIGTERM before SIGKILL.
GRACE_SECONDS = 10

Outcome = Literal["passed", "failed", "timed out", "skipped"]


@dataclass
class Result:
    slug: str
    path: str
    owner: str
    outcome: Outcome
    reason: str = ""
    seconds: float = 0.0
    command: str = ""

    @property
    def ok(self) -> bool:
        return self.outcome in ("passed", "skipped")


# Selection -----------------------------------------------------------------


def changed_files(base: str, root: Path = REPO_ROOT) -> list[str]:
    """Files changed on this branch since it left ``base`` (a git ref)."""
    out = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [line.strip() for line in out.splitlines() if line.strip()]


def affected_by(example: Example, files: Sequence[str]) -> bool:
    if example.kind == "folder":
        return any(f.startswith(example.path + "/") for f in files)
    return example.path in files


def select(
    examples: Sequence[Example],
    *,
    slugs: Sequence[str] = (),
    changed: Sequence[str] | None = None,
    run_all: bool = False,
    product: str | None = None,
) -> tuple[list[Example], list[str]]:
    """Pick examples to run. Returns (examples, errors)."""
    errors: list[str] = []
    if slugs:
        by_slug = {e.slug: e for e in examples}
        errors = [f"no example with slug {s!r}" for s in slugs if s not in by_slug]
        picked = [by_slug[s] for s in slugs if s in by_slug]
    elif changed is not None and not any(f in RUNNER_FILES for f in changed):
        picked = [e for e in examples if affected_by(e, changed)]
    elif changed is not None or run_all:
        # Every maintained example: frozen demos are pinned and never re-run.
        picked = [e for e in examples if e.meta.status == "maintained"]
    else:
        picked = []

    if product:
        picked = [e for e in picked if product in e.meta.product]
    return picked, errors


# Commands ------------------------------------------------------------------


def build_command(
    example: Example,
    *,
    upgrade: Sequence[str] = (),
    prerelease: bool = False,
) -> tuple[list[str], str]:
    """Return (argv, working directory relative to the repo root)."""
    meta = example.meta
    uv_flags: list[str] = []
    if prerelease:
        uv_flags += ["--prerelease", "allow"]
        # A lockfile can't be used as-is with a different pre-release policy,
        # so re-resolve what the example targets when nothing else is named.
        upgrade = upgrade or list(meta.targets)

    if example.kind == "folder":
        entry = meta.entrypoint or "main.py"
        if upgrade:
            # Re-resolve the named packages instead of trusting the lockfile.
            lock = [f for pkg in upgrade for f in ("--upgrade-package", pkg)]
        else:
            lock = ["--locked"]
        uv = ["uv", "run", "--project", ".", *lock, *uv_flags]
        if meta.test == "import-only":
            return [*uv, "python", "-c", IMPORT_ONLY, entry], example.path
        return [*uv, "python", entry], example.path

    packages = [f"{pkg}{spec}" for pkg, spec in meta.targets.items()]
    packages += list(meta.dependencies or [])
    refresh = [f for pkg in upgrade for f in ("--refresh-package", pkg)]
    uv = [
        "uv",
        "run",
        "--isolated",
        "--no-project",
        *refresh,
        *uv_flags,
        *[f for p in packages for f in ("--with", p)],
    ]
    if meta.test == "import-only":
        return [*uv, "python", "-c", IMPORT_ONLY, example.path], "."
    if meta.cmd:
        return [*uv, *meta.cmd, *(meta.args or [])], "."
    return [*uv, "python", example.path, *(meta.args or [])], "."


# Running -------------------------------------------------------------------


def _in_actions() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


def run_process_group(
    argv: list[str], *, cwd: Path, env: dict[str, str], timeout: int
) -> int:
    """Run argv in its own process group and return its exit code.

    On timeout the whole group is ended, not just ``uv``, so an example's own
    processes can't keep running into the next example. Raises
    ``subprocess.TimeoutExpired`` after cleaning up.
    """
    proc = subprocess.Popen(argv, cwd=cwd, env=env, start_new_session=True)
    try:
        return proc.wait(timeout=timeout)
    except BaseException:  # the timeout, or Ctrl-C while running locally
        _end_group(proc)
        raise


def _end_group(proc: subprocess.Popen) -> None:
    if not hasattr(os, "killpg"):  # Windows
        proc.kill()
        proc.wait()
        return
    try:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.wait(timeout=GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            pass
        # The group can outlive its leader, so always finish it off.
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass  # every process in the group has exited
    proc.wait()


def run_example(
    example: Example,
    root: Path = REPO_ROOT,
    *,
    command: tuple[list[str], str] | None = None,
    upgrade: Sequence[str] = (),
    prerelease: bool = False,
    run: Callable[..., int] = run_process_group,
) -> Result:
    meta = example.meta
    result = Result(example.slug, example.path, meta.owner, "skipped")

    if meta.test == "skip":
        result.reason = "test: skip"
        return result
    missing = [name for name in meta.requires_secrets if not os.environ.get(name)]
    if missing:
        result.reason = f"missing secrets: {', '.join(missing)}"
        return result

    argv, cwd = command or build_command(
        example, upgrade=upgrade, prerelease=prerelease
    )
    result.command = " ".join(argv)
    env = os.environ | (meta.env or {})

    print(f"::group::{example.slug}" if _in_actions() else f"== {example.slug}")
    print(f"$ (cd {cwd} && {result.command})", flush=True)
    start = time.monotonic()
    try:
        returncode = run(argv, cwd=root / cwd, env=env, timeout=meta.timeout)
    except subprocess.TimeoutExpired:
        result.outcome = "timed out"
        result.reason = f"no exit after {meta.timeout}s"
    except OSError as exc:
        result.outcome = "failed"
        result.reason = str(exc)
    else:
        if returncode == 0:
            result.outcome = "passed"
        else:
            result.outcome = "failed"
            result.reason = f"exit code {returncode}"
    result.seconds = round(time.monotonic() - start, 1)
    if _in_actions():
        print("::endgroup::")
    print(f"{example.slug}: {result.outcome} {result.reason}".rstrip(), flush=True)
    return result


def summary_markdown(results: Sequence[Result]) -> str:
    if not results:
        return "No examples to run.\n"
    rows = [
        f"| `{r.slug}` | {r.outcome} | {r.reason} | {r.seconds}s |" for r in results
    ]
    counts = {o: sum(r.outcome == o for r in results) for o in Outcome.__args__}
    totals = ", ".join(f"{n} {o}" for o, n in counts.items() if n)
    return "\n".join(
        [
            f"**Examples:** {totals}",
            "",
            "| Example | Outcome | Reason | Time |",
            "| --- | --- | --- | --- |",
            *rows,
            "",
        ]
    )


# Failure issues --------------------------------------------------------------


def issue_title(result: Result) -> str:
    return f"Example failing: {result.slug}"


def issue_body(result: Result, run_url: str, trigger: str) -> str:
    return (
        f"`{result.path}` {result.outcome} in the {trigger} run: {result.reason}.\n\n"
        f"- Owner: {result.owner}\n"
        f"- Run: {run_url}\n"
        f"- Command: `{result.command}`\n\n"
        "Maintained examples that stay red for 30 days move to `frozen` or are "
        "deleted. See the consolidation plan's lifecycle rules.\n"
    )


def open_issues(results_file: Path, *, gh: Callable[..., str] | None = None) -> int:
    """Open (or comment on) one issue per failed example."""
    gh = gh or _gh
    results = [Result(**r) for r in json.loads(results_file.read_text())]
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "PrefectHQ/examples")
    run_url = f"{server}/{repo}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    trigger = os.environ.get("EXAMPLES_TRIGGER", "scheduled")

    for result in results:
        if result.ok:
            continue
        title = issue_title(result)
        body = issue_body(result, run_url, trigger)
        found = json.loads(
            gh(
                "issue",
                "list",
                "--state",
                "open",
                "--search",
                f'in:title "{title}"',
                "--json",
                "number,title",
            )  # fmt: skip
        )
        existing = [i["number"] for i in found if i["title"] == title]
        if existing:
            gh("issue", "comment", str(existing[0]), "--body", body)
            print(f"Commented on #{existing[0]} for {result.slug}")
        else:
            gh("issue", "create", "--title", title, "--body", body)
            print(f"Opened an issue for {result.slug}")
    return 0


def _gh(*args: str) -> str:
    return subprocess.run(
        ["gh", *args], capture_output=True, text=True, check=True
    ).stdout


# CLI -------------------------------------------------------------------------


def main(argv: list[str] | None = None, root: Path = REPO_ROOT) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m internal.runner", description="Run examples"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Run examples")
    run_p.add_argument("slugs", nargs="*", default=[], help="Example slugs")
    run_p.add_argument(
        "--changed-since",
        metavar="REF",
        help="Run examples changed since REF (such as origin/main)",
    )
    run_p.add_argument(
        "--all", action="store_true", help="Run every maintained example"
    )
    run_p.add_argument("--product", choices=PRODUCTS, help="Only this product")
    run_p.add_argument(
        "--upgrade",
        action="append",
        default=[],
        metavar="PACKAGE",
        help="Test against the newest release of PACKAGE instead of the lockfile",
    )
    run_p.add_argument(
        "--prerelease", action="store_true", help="Allow pre-release versions"
    )
    run_p.add_argument("--results", type=Path, help="Write results as JSON here")
    run_p.add_argument("--dry-run", action="store_true", help="List, don't run")

    issues_p = sub.add_parser(
        "open-issues", help="Open an issue for each failure in a results file"
    )
    issues_p.add_argument("results", type=Path)

    args = parser.parse_args(argv)
    if args.command == "open-issues":
        return open_issues(args.results)
    if sum([bool(args.slugs), bool(args.changed_since), args.all]) != 1:
        run_p.error("give example slugs, --changed-since REF or --all (just one)")

    found = discover(root)
    if found.errors:
        print("Examples break the contract; run `python -m internal.catalog --check`.")
        for error in found.errors:
            print(f"  - {error}")
        return 2

    changed = changed_files(args.changed_since, root) if args.changed_since else None
    picked, errors = select(
        found.examples,
        slugs=args.slugs,
        changed=changed,
        run_all=args.all,
        product=args.product,
    )
    for error in errors:
        print(error)
    if errors:
        return 2

    if args.dry_run or not picked:
        print(f"{len(picked)} example(s) to run")
        for example in picked:
            print(f"  - {example.slug} ({example.path})")
        return 0

    results = [
        run_example(e, root, upgrade=args.upgrade, prerelease=args.prerelease)
        for e in picked
    ]

    summary = summary_markdown(results)
    print(summary)
    if path := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(path, "a", encoding="utf-8") as f:
            f.write(summary)
    if args.results:
        args.results.write_text(json.dumps([asdict(r) for r in results], indent=2))
    return 0 if all(r.ok for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
