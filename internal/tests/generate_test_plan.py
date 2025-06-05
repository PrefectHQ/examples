#!/usr/bin/env python3
"""
Generate a test plan based on changed files.

This script takes a list of changed files (e.g., from a GitHub Action when a PR is
created or updated) and generates a test plan to test just those examples.
"""

import argparse
import json
import os
import sys

from ..utils import Example, get_examples


def get_changed_files_from_env() -> list[str]:
    """Get changed files from GitHub Actions environment variables."""
    if "GITHUB_EVENT_PATH" in os.environ:
        with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as f:
            event = json.load(f)

        # Extract changed files from the pull request
        if "pull_request" in event:
            files = []
            if "changed_files" in event["pull_request"]:
                for file_info in event["pull_request"]["changed_files"]:
                    files.append(file_info["filename"])
            return files

    return []


def get_changed_files_from_git_diff(commit_range: str) -> list[str]:
    """Get changed files from git diff in the given commit range."""
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only", commit_range],
        capture_output=True,
        text=True,
        check=True,
    )

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def get_examples_to_test(changed_files: list[str]) -> list[Example]:
    """Get examples to test based on changed files."""
    examples = get_examples()

    # If internal tools have changed, test all examples
    for file in changed_files:
        if file.startswith("internal/"):
            print(f"Internal tools changed ({file}), testing all examples")
            return examples

    # Get all Python files that have changed
    changed_py_files = {
        f
        for f in changed_files
        if f.endswith(".py")
        and f.startswith("examples/")
        and not f.endswith("__init__.py")
    }

    # Find examples that correspond to changed files
    examples_to_test = []
    for example in examples:
        if example.repo_filename in changed_py_files:
            examples_to_test.append(example)

    return examples_to_test


def output_test_plan(examples: list[Example], format: str = "text"):
    """Output the test plan in the specified format."""
    if not examples:
        print("No examples to test.")
        return

    if format == "json":
        example_dicts = [example.dict() for example in examples]
        print(json.dumps(example_dicts, indent=2))
    else:
        print(f"Test plan: {len(examples)} examples to test")
        for example in examples:
            print(f"- {example.repo_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a test plan based on changed files"
    )
    parser.add_argument(
        "--github-action",
        action="store_true",
        help="Get changed files from GitHub Actions environment",
    )
    parser.add_argument(
        "--git-diff",
        help="Get changed files from git diff in the given commit range (e.g., 'HEAD^..HEAD')",
    )
    parser.add_argument(
        "--changed-files", nargs="+", help="Explicitly specify changed files"
    )
    parser.add_argument(
        "--format", choices=["text", "json"], default="text", help="Output format"
    )

    args = parser.parse_args()

    # Get changed files
    changed_files = []
    if args.github_action:
        changed_files = get_changed_files_from_env()
    elif args.git_diff:
        changed_files = get_changed_files_from_git_diff(args.git_diff)
    elif args.changed_files:
        changed_files = args.changed_files
    else:
        parser.error(
            "Must specify one of --github-action, --git-diff, or --changed-files"
        )

    # Get examples to test
    examples_to_test = get_examples_to_test(changed_files)

    # Output test plan
    output_test_plan(examples_to_test, args.format)

    # Return an error code if no examples to test
    return 0 if examples_to_test else 1


if __name__ == "__main__":
    sys.exit(main())
