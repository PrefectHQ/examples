import os
import random
import subprocess
import sys
import time
from pathlib import Path

from .utils import get_examples

MINUTES = 60
TIMEOUT = 10 * MINUTES  # 10 minutes timeout for running examples


def run_script(example):
    """Run a single example script and return its exit code."""
    t0 = time.time()

    print(f"Running: {example.repo_filename}")
    print(f"CLI args: {example.cli_args}")
    
    try:
        process = subprocess.run(
            [str(x) for x in example.cli_args],
            env=os.environ | (example.env or {}),
            timeout=TIMEOUT,
        )
        total_time = time.time() - t0
        
        if process.returncode == 0:
            print(f"Success after {total_time:.2f}s ✅")
        else:
            print(
                f"Failed after {total_time:.2f}s with return code {process.returncode} ❌"
            )
        return process.returncode
    except subprocess.TimeoutExpired:
        total_time = time.time() - t0
        print(f"Timed out after {total_time:.2f}s ⏱️")
        return 1
    except Exception as e:
        total_time = time.time() - t0
        print(f"Failed after {total_time:.2f}s with exception: {e} ❌")
        return 1


def list_examples():
    """List all examples in the repository."""
    examples = get_examples()
    
    if not examples:
        print("No examples found.")
        return
    
    print(f"Found {len(examples)} examples:")
    for example in sorted(examples, key=lambda e: e.repo_filename):
        deploy_status = "✅" if example.metadata and example.metadata.get("deploy", False) else "❌"
        print(f"{deploy_status} {example.repo_filename}")


def run_single_example(example_name_or_path):
    """Run a single example by name or path."""
    examples = get_examples()
    
    # First try exact path match
    matching_examples = [e for e in examples if e.repo_filename == example_name_or_path]
    
    # If no exact match, try stem match
    if not matching_examples:
        matching_examples = [e for e in examples if e.stem == example_name_or_path]
    
    # If still no match, try partial path match
    if not matching_examples:
        matching_examples = [e for e in examples if example_name_or_path in e.repo_filename]
    
    if not matching_examples:
        print(f"No examples found matching '{example_name_or_path}'")
        return 1
    
    if len(matching_examples) > 1:
        print(f"Multiple examples found matching '{example_name_or_path}':")
        for e in matching_examples:
            print(f"- {e.repo_filename}")
        return 1
    
    return run_script(matching_examples[0])


def run_random_example():
    """Run a random example from the repository."""
    examples = get_examples()
    
    if not examples:
        print("No examples found.")
        return 1
    
    example = random.choice(examples)
    return run_script(example)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m internal.run_example <example_name_or_path>")
        sys.exit(1)
    
    example_name_or_path = sys.argv[1]
    sys.exit(run_single_example(example_name_or_path)) 