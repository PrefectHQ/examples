"""Tests for selecting, building commands for and running examples."""

import json
import subprocess
import sys

import pytest

from .. import runner
from ..catalog import discover
from ..runner import Result, build_command, main, run_example, select
from .test_catalog import FILE_EXAMPLE, FOLDER_MANIFEST, folder_example, write

DEMO = FILE_EXAMPLE.replace('">=3.4"', '"==3.4.11"').replace(
    "# tags:", "# product: prefect\n# tags:"
)


def with_fields(text: str, fields: str) -> str:
    """Add frontmatter lines to FILE_EXAMPLE-style text."""
    return text.replace("# tags:", f"{fields}\n# tags:")


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "prefect/hello.py", FILE_EXAMPLE)
    folder_example(tmp_path, "fastmcp/servers/weather")
    write(tmp_path, "demos/2026-pycon-hello.py", DEMO)
    return tmp_path


def examples(root):
    found = discover(root)
    assert found.errors == []
    return found.examples


def by_slug(root, slug):
    return next(e for e in examples(root) if e.slug == slug)


# Selection -------------------------------------------------------------------


def test_select_by_slug(repo):
    picked, errors = select(examples(repo), slugs=["weather"])
    assert [e.slug for e in picked] == ["weather"]
    assert errors == []


def test_select_unknown_slug(repo):
    _, errors = select(examples(repo), slugs=["nope"])
    assert errors == ["no example with slug 'nope'"]


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        (["prefect/hello.py"], ["hello"]),
        (["fastmcp/servers/weather/uv.lock"], ["weather"]),
        (["fastmcp/servers/weather-extra/x.py"], []),  # prefix, not the folder
        (["README.md"], []),
        (["demos/2026-pycon-hello.py"], ["2026-pycon-hello"]),
    ],
)
def test_select_changed(repo, changed, expected):
    picked, _ = select(examples(repo), changed=changed)
    assert [e.slug for e in picked] == expected


def test_runner_change_runs_every_maintained_example(repo):
    picked, _ = select(examples(repo), changed=["internal/runner.py"])
    assert {e.slug for e in picked} == {"hello", "weather"}  # not the frozen demo


def test_all_skips_frozen_and_filters_product(repo):
    picked, _ = select(examples(repo), run_all=True)
    assert {e.slug for e in picked} == {"hello", "weather"}
    picked, _ = select(examples(repo), run_all=True, product="fastmcp")
    assert [e.slug for e in picked] == ["weather"]


def test_changed_files_diffs_against_merge_base(tmp_path):
    def git(*args):
        subprocess.run(
            ["git", "-c", "user.name=t", "-c", "user.email=t@t", *args],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

    git("init", "-q", "-b", "main")
    write(tmp_path, "a.py", "1")
    git("add", ".")
    git("commit", "-qm", "base")
    git("checkout", "-qb", "feature")
    write(tmp_path, "prefect/hello.py", "2")
    git("add", ".")
    git("commit", "-qm", "change")
    git("checkout", "-q", "main")
    write(tmp_path, "b.py", "3")  # a later change on main is not ours
    git("add", ".")
    git("commit", "-qm", "main moves on")
    git("checkout", "-q", "feature")

    assert runner.changed_files("main", tmp_path) == ["prefect/hello.py"]


# Commands --------------------------------------------------------------------


def test_file_command(repo):
    argv, cwd = build_command(by_slug(repo, "hello"))
    assert cwd == "."
    assert argv == [
        "uv", "run", "--isolated", "--no-project", "--with", "prefect>=3.4",
        "python", "prefect/hello.py",
    ]  # fmt: skip


def test_file_command_with_dependencies_and_cmd(tmp_path):
    write(
        tmp_path,
        "prefect/hello.py",
        with_fields(
            FILE_EXAMPLE,
            "# dependencies: [pandas]\n# cmd: [prefect, run]\n# args: [--quiet]",
        ),
    )
    argv, _ = build_command(by_slug(tmp_path, "hello"))
    assert argv[-7:] == [
        "--with", "prefect>=3.4", "--with", "pandas", "prefect", "run", "--quiet",
    ]  # fmt: skip


def test_folder_command_uses_its_lockfile(tmp_path):
    folder_example(
        tmp_path,
        "fastmcp/servers/weather",
        FOLDER_MANIFEST.replace("test: import-only\n", ""),
    )
    argv, cwd = build_command(by_slug(tmp_path, "weather"))
    assert cwd == "fastmcp/servers/weather"
    assert argv == ["uv", "run", "--project", ".", "--locked", "python", "main.py"]


def test_folder_command_import_only(repo):
    # FOLDER_MANIFEST sets test: import-only
    weather = by_slug(repo, "weather")
    assert weather.meta.test == "import-only"
    argv, _ = build_command(weather)
    assert argv[-4:] == ["python", "-c", runner.IMPORT_ONLY, "main.py"]


def test_upgrade_and_prerelease(repo):
    argv, _ = build_command(
        by_slug(repo, "weather"), upgrade=["fastmcp"], prerelease=True
    )
    assert "--locked" not in argv
    assert argv[:8] == [
        "uv", "run", "--project", ".", "--upgrade-package", "fastmcp",
        "--prerelease", "allow",
    ]  # fmt: skip

    argv, _ = build_command(by_slug(repo, "hello"), upgrade=["prefect"])
    assert argv[4:6] == ["--refresh-package", "prefect"]


# Running ---------------------------------------------------------------------


def python(code: str) -> tuple[list[str], str]:
    return [sys.executable, "-c", code], "."


def test_run_passes_and_fails(repo):
    hello = by_slug(repo, "hello")
    assert run_example(hello, repo, command=python("pass")).outcome == "passed"
    result = run_example(hello, repo, command=python("raise SystemExit(3)"))
    assert (result.outcome, result.reason) == ("failed", "exit code 3")
    assert not result.ok


def test_run_times_out(tmp_path):
    write(tmp_path, "prefect/hello.py", with_fields(FILE_EXAMPLE, "# timeout: 1"))
    result = run_example(
        by_slug(tmp_path, "hello"),
        tmp_path,
        command=python("import time; time.sleep(10)"),
    )
    assert result.outcome == "timed out"


def test_run_sets_example_env(tmp_path):
    write(
        tmp_path,
        "prefect/hello.py",
        with_fields(FILE_EXAMPLE, "# env:\n#   GREETING: hi"),
    )
    code = "import os; raise SystemExit(os.environ['GREETING'] != 'hi')"
    result = run_example(by_slug(tmp_path, "hello"), tmp_path, command=python(code))
    assert result.outcome == "passed"


def test_skip_and_missing_secrets(tmp_path, monkeypatch):
    write(tmp_path, "prefect/skipped.py", with_fields(FILE_EXAMPLE, "# test: skip"))
    write(
        tmp_path,
        "prefect/cloud.py",
        with_fields(FILE_EXAMPLE, "# requires_secrets: [PREFECT_API_KEY]"),
    )
    monkeypatch.delenv("PREFECT_API_KEY", raising=False)

    def explode(*args, **kwargs):
        raise AssertionError("should not run")

    for slug, reason in [
        ("skipped", "test: skip"),
        ("cloud", "missing secrets: PREFECT_API_KEY"),
    ]:
        result = run_example(by_slug(tmp_path, slug), tmp_path, run=explode)
        assert (result.outcome, result.reason) == ("skipped", reason)
        assert result.ok


# CLI ---------------------------------------------------------------------------


def test_main_dry_run(repo, capsys):
    assert main(["run", "--all", "--dry-run"], root=repo) == 0
    out = capsys.readouterr().out
    assert "2 example(s) to run" in out
    assert "2026-pycon-hello" not in out


def test_main_needs_exactly_one_selection(repo):
    with pytest.raises(SystemExit):
        main(["run"], root=repo)
    with pytest.raises(SystemExit):
        main(["run", "hello", "--all"], root=repo)


def test_main_unknown_slug(repo):
    assert main(["run", "nope"], root=repo) == 2


def test_main_contract_errors(tmp_path):
    write(tmp_path, "prefect/bad.py", "x = 1\n")
    assert main(["run", "--all"], root=tmp_path) == 2


def test_main_writes_results_and_summary(repo, tmp_path, monkeypatch):
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("WEATHER_API_KEY", "test")  # weather requires it
    monkeypatch.setattr(
        runner,
        "build_command",
        lambda example, **_: python("raise SystemExit(1)")
        if example.slug == "weather"
        else python("pass"),
    )
    results_file = tmp_path / "results.json"

    assert main(["run", "--all", "--results", str(results_file)], root=repo) == 1
    results = {r["slug"]: r["outcome"] for r in json.loads(results_file.read_text())}
    assert results == {"weather": "failed", "hello": "passed"}
    assert "1 passed, 1 failed" in summary.read_text()


# Failure issues ----------------------------------------------------------------


def test_open_issues_creates_then_comments(tmp_path):
    results = [
        Result("hello", "prefect/hello.py", "@PrefectHQ/devrel", "passed"),
        Result("weather", "fastmcp/servers/weather", "@octocat", "failed", "exit 1"),
        Result("slow", "prefect/slow.py", "@octocat", "timed out", "no exit"),
    ]
    results_file = tmp_path / "results.json"
    results_file.write_text(json.dumps([r.__dict__ for r in results]))

    calls = []

    def gh(*args):
        calls.append(args)
        if args[:2] == ("issue", "list"):
            existing = [{"number": 7, "title": "Example failing: slow"}]
            return json.dumps(existing if "slow" in args[5] else [])
        return ""

    assert runner.open_issues(results_file, gh=gh) == 0
    actions = [c[:2] for c in calls if c[1] != "list"]
    assert actions == [("issue", "create"), ("issue", "comment")]
    create = next(c for c in calls if c[1] == "create")
    assert "Example failing: weather" in create
    assert "@octocat" in create[-1]
    assert next(c for c in calls if c[1] == "comment")[2] == "7"
