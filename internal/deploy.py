#!/usr/bin/env python3
"""
Script to deploy Prefect flows from examples.

This script looks for examples with a `deploy: true` flag in their frontmatter
and deploys them using the Prefect API.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from .utils import Example, ExampleType, get_examples


def deploy_example(example: Example) -> int:
    """Deploy a single example using Prefect."""
    if not example.metadata:
        print(f"Example {example.repo_filename} has no metadata, skipping")
        return 0
    
    if not example.metadata.get("deploy", False):
        print(f"Example {example.repo_filename} is not marked for deployment, skipping")
        return 0
    
    if not example.cli_args:
        print(f"Example {example.repo_filename} has no deployment command, skipping")
        return 0
    
    print(f"Deploying {example.repo_filename}...")
    print(f"Command: {' '.join(str(arg) for arg in example.cli_args)}")
    
    try:
        process = subprocess.run(
            [str(arg) for arg in example.cli_args],
            env=os.environ | (example.metadata.get("env", {})),
            check=True,
        )
        print(f"Successfully deployed {example.repo_filename} ✅")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Failed to deploy {example.repo_filename}: {e} ❌")
        return 1


def deploy_examples(examples: Optional[List[Example]] = None) -> int:
    """Deploy all examples marked for deployment."""
    if examples is None:
        examples = get_examples()
    
    # Filter examples that should be deployed
    examples_to_deploy = [
        e for e in examples
        if e.type == ExampleType.MODULE
        and e.metadata
        and e.metadata.get("deploy", False)
        and e.cli_args
    ]
    
    if not examples_to_deploy:
        print("No examples found to deploy")
        return 0
    
    print(f"Found {len(examples_to_deploy)} examples to deploy")
    
    failed = 0
    for example in examples_to_deploy:
        result = deploy_example(example)
        if result != 0:
            failed += 1
    
    if failed > 0:
        print(f"Failed to deploy {failed} examples ❌")
        return 1
    
    print(f"Successfully deployed {len(examples_to_deploy)} examples ✅")
    return 0


def main():
    """Main entry point for the deploy script."""
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description="Deploy Prefect examples")
    parser.add_argument(
        "-e", "--example",
        help="Deploy a specific example by name or path",
    )
    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="Deploy all examples marked for deployment",
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List examples that would be deployed but don't deploy them",
    )
    
    args = parser.parse_args()
    
    if args.list:
        examples = get_examples()
        examples_to_deploy = [
            e for e in examples
            if e.type == ExampleType.MODULE
            and e.metadata
            and e.metadata.get("deploy", False)
            and e.cli_args
        ]
        
        if not examples_to_deploy:
            print("No examples found to deploy")
            return 0
        
        print(f"Found {len(examples_to_deploy)} examples that would be deployed:")
        for example in examples_to_deploy:
            print(f"- {example.repo_filename}")
            if example.cli_args:
                print(f"  Command: {' '.join(str(arg) for arg in example.cli_args)}")
        return 0
    
    if args.example:
        examples = get_examples()
        matching_examples = [e for e in examples if e.repo_filename == args.example or args.example in e.repo_filename]
        
        if not matching_examples:
            print(f"No examples found matching '{args.example}'")
            return 1
        
        if len(matching_examples) > 1:
            print(f"Multiple examples found matching '{args.example}':")
            for e in matching_examples:
                print(f"- {e.repo_filename}")
            return 1
        
        return deploy_example(matching_examples[0])
    
    if args.all:
        return deploy_examples()
    
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main()) 