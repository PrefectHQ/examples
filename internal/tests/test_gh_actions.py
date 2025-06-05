"""
This module contains tests for the GitHub Actions workflow.

It is designed to replicate the behaviour of the workflow when run locally.

The workflow is designed to run on every push to the repository, and is
configured to run on every push to the designated branch.
"""

import os
import subprocess
from pathlib import Path

import pytest

# Re-use the helper from the existing local script so behaviour stays exactly the same
from .test_examples import run_example  # type: ignore


def _git_diff_names(*args: str) -> list[str]:
    """Return the lines from a `git diff --name-only` call.

    If the call fails (e.g. not a git repo) an empty list is returned.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", *args],
            capture_output=True,
            text=True,
            check=True,
        )
        return [line.strip() for line in result.stdout.splitlines() if line.strip()]
    except Exception:
        return []


def _discover_changed_example_files() -> list[str]:
    """Return a list of example .py files that have changed relative to *origin/examples-markdown*.

    Behavioural differences from the GitHub Action:
    •  We *always* compute the diff instead of trusting `CHANGED_FILES` – this
       guarantees up-to-date results when running locally many times.
    •  We also include *working-tree* changes (unstaged / uncommitted) so that
       you can iterate without committing after every edit.
    """

    # 1) Files changed in commits that are ahead of origin/examples-markdown
    committed = _git_diff_names("origin/examples-markdown..HEAD")

    # 2) Files modified in the working tree that are not yet committed
    #    (equivalent to `git diff --name-only` with no range specified).
    uncommitted = _git_diff_names()

    candidates = sorted(set(committed + uncommitted))

    # Filter to Python example files and exclude dunders.
    example_files: list[str] = [
        f
        for f in candidates
        if f.startswith("examples/") and f.endswith(".py") and "__" not in Path(f).name
    ]

    # Keep only files that still exist locally (they might have been deleted).
    example_files = [f for f in example_files if Path(f).exists()]

    # Update CHANGED_FILES so any downstream code that relies on it still works.
    os.environ["CHANGED_FILES"] = " ".join(example_files)

    return example_files


# Collect the examples right away so pytest can parametrize at collection time.
_changed_examples = _discover_changed_example_files()

# --- Expected-failure examples ------------------------------------------------
# Some examples demonstrate Prefect retry semantics by ultimately exiting with a
# non-zero status.  Running them as-is in CI will therefore "fail" even though
# the behaviour is correct.  List such files here so the test is marked as
# xfail rather than fail.
#
# Paths are stored **relative** to the repository root, matching what
# _discover_changed_example_files returns.

_xfail_examples = {
    "examples/04_misc/04_retries.py",
}

# --- Tests -------------------------------------------------------------------


@pytest.mark.skipif(
    not _changed_examples, reason="No changed example files detected – nothing to test."
)
@pytest.mark.parametrize("example_path", _changed_examples, ids=lambda p: p)
def test_changed_example(example_path: str):
    """Run each changed example exactly like the GitHub Action does."""
    passed = run_example(example_path)

    if example_path in _xfail_examples:
        pytest.xfail("Example is expected to exit non-zero (demonstrates retries)")

    assert passed, f"Example {example_path} failed"
