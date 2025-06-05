#!/usr/bin/env python3
"""
Test Prefect examples locally.

This script mimics the GitHub workflow behavior to test Prefect examples,
removing frontmatter before execution and reporting success/failure.
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
from typing import Any


def parse_frontmatter(content: str) -> tuple[dict[str, Any] | None, str]:
    """Parse and remove frontmatter from file content."""
    # Simple function to remove frontmatter between --- markers
    frontmatter_pattern = re.compile(r"^---\s*$(.*?)^---\s*$", re.MULTILINE | re.DOTALL)
    match = frontmatter_pattern.search(content)

    if match:
        # Remove the frontmatter
        content_without_frontmatter = content[: match.start()] + content[match.end() :]
        return {}, content_without_frontmatter.strip()

    return None, content


def run_example(file_path: str) -> bool:
    """Run a single example file and return True if it passes, False otherwise."""
    print(f"Testing example: {file_path}")
    print("--------------------------------------")

    # Create a temporary file with frontmatter removed
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
        temp_path = temp_file.name

        # Read the original file
        with open(file_path) as f:
            content = f.read()

        # Remove frontmatter
        _, content_without_frontmatter = parse_frontmatter(content)

        # Write cleaned content to temp file
        temp_file.write(content_without_frontmatter.encode())

    try:
        # Run the example
        result = subprocess.run(
            [sys.executable, temp_path], capture_output=True, text=True, check=False
        )

        # Print output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)

        # Check if it passed
        if result.returncode == 0:
            print(f"✅ Example {file_path} passed.")
            return True
        else:
            print(f"❌ Example {file_path} failed with exit code {result.returncode}.")
            return False
    except Exception as e:
        print(f"❌ Example {file_path} failed with exception: {e}")
        return False
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        print("--------------------------------------")


def test_examples(files: list[str]) -> tuple[int, int]:
    """Test multiple example files and return counts of passed and failed tests."""
    if not files:
        print("No examples to test.")
        return 0, 0

    passed = 0
    failed = 0

    for file_path in files:
        if run_example(file_path):
            passed += 1
        else:
            failed += 1

    return passed, failed


def find_example_files(
    directory: str = "examples", extensions: list[str] | None = None
) -> list[str]:
    """Find all example files in the given directory."""

    extensions = extensions or [".py"]

    example_files = []
    for root, _, files in os.walk(directory):
        # Skip internal directories
        if "internal" in root.split(os.path.sep):
            continue

        for file in files:
            if any(file.endswith(ext) for ext in extensions) and not file.startswith(
                "__"
            ):
                path = os.path.join(root, file)
                example_files.append(path)

    return example_files


def main():
    parser = argparse.ArgumentParser(description="Test Prefect examples locally")
    parser.add_argument("files", nargs="*", help="Specific example files to test")
    parser.add_argument(
        "--all", action="store_true", help="Test all examples in the repository"
    )
    parser.add_argument(
        "--dir",
        default="examples",
        help="Directory to search for examples when using --all",
    )

    args = parser.parse_args()

    # Determine which files to test
    if args.all:
        files = find_example_files(args.dir)
    else:
        files = args.files

    if not files:
        print(
            "No files specified. Use --all to test all examples or provide specific files."
        )
        return 1

    print(f"Running tests for {len(files)} examples:")
    for f in files:
        print(f"- {f}")
    print("======================================")

    # Run the tests
    passed, failed = test_examples(files)

    # Print summary
    print("======================================")
    print(f"Test Results: {passed} passed, {failed} failed")

    # Return non-zero exit code if any tests failed
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
