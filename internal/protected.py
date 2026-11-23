"""Check that paths other repositories load from this repo still exist.

The list lives in ``internal/protected_paths.yaml`` and who depends on each
path is documented in ``internal/DOWNSTREAM.md``.

Usage::

    python -m internal.protected
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTECTED_FILE = Path(__file__).resolve().parent / "protected_paths.yaml"


def _defines_function(source: str, name: str) -> bool:
    tree = ast.parse(source)
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name
        for node in tree.body
    )


def check_protected(
    root: Path = REPO_ROOT, config_file: Path = PROTECTED_FILE
) -> list[str]:
    """Return a list of problems; an empty list means every protected path is intact."""
    config = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    problems: list[str] = []

    for entrypoint in config.get("entrypoints", []):
        file_part, _, func = entrypoint.rpartition(":")
        if not file_part or not func:
            problems.append(f"{entrypoint}: expected '<file>:<function>'")
            continue
        path = root / file_part
        if not path.is_file():
            problems.append(f"{entrypoint}: file {file_part} is missing")
            continue
        if not _defines_function(path.read_text(encoding="utf-8"), func):
            problems.append(
                f"{entrypoint}: {file_part} no longer defines a top-level '{func}'"
            )

    for rel in config.get("paths", []):
        if not (root / rel).exists():
            problems.append(f"{rel}: path is missing")

    return problems


def main() -> int:
    problems = check_protected()
    if problems:
        print("Protected paths changed. Other repos load these from main:")
        for problem in problems:
            print(f"  - {problem}")
        print(
            "\nSee internal/DOWNSTREAM.md. Update the dependents first, then edit "
            "internal/protected_paths.yaml in the same PR."
        )
        return 1
    print("All protected paths are intact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
