#!/usr/bin/env python3
"""
Main entry point for running the internal tools.
"""

import argparse
import sys
from .utils import get_examples
from .run_example import run_script, run_single_example, run_random_example, list_examples

def main():
    parser = argparse.ArgumentParser(
        description="Prefect Examples internal tools",
        prog="python -m internal"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # run-example command
    run_parser = subparsers.add_parser("run-example", help="Run an example")
    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument("-e", "--example", help="Run a specific example by stem name or path")
    run_group.add_argument("-r", "--random", action="store_true", help="Run a random example")
    run_group.add_argument("-l", "--list", action="store_true", help="List all available examples")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all examples")
    
    # Generate docs command
    docs_parser = subparsers.add_parser("generate-docs", help="Generate documentation from examples")
    docs_parser.add_argument(
        "-o", "--output-dir",
        default="docs",
        help="Output directory for documentation files (default: docs)"
    )
    docs_parser.add_argument(
        "-e", "--extension",
        default=".mdx",
        choices=[".md", ".mdx"],
        help="File extension for documentation files (default: .mdx)"
    )
    
    # generate-test-plan command
    test_plan_parser = subparsers.add_parser("test-plan", help="Generate a test plan")
    test_plan_parser.add_argument("--github-action", action="store_true", 
                         help="Get changed files from GitHub Actions environment")
    test_plan_parser.add_argument("--git-diff", 
                         help="Get changed files from git diff in the given commit range (e.g., 'HEAD^..HEAD')")
    test_plan_parser.add_argument("--changed-files", nargs="+", 
                         help="Explicitly specify changed files")
    test_plan_parser.add_argument("--format", choices=["text", "json"], default="text",
                         help="Output format")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    if args.command == "run-example":
        if args.list:
            list_examples()
            return 0
        elif args.random:
            return run_random_example()
        elif args.example:
            return run_single_example(args.example)
    elif args.command == "list":
        list_examples()
        return 0
    elif args.command == "generate-docs":
        from .generate_docs import generate_docs
        return generate_docs(args.output_dir, args.extension)
    elif args.command == "test-plan":
        from .tests.generate_test_plan import main as test_plan_main
        
        test_plan_argv = []
        if args.github_action:
            test_plan_argv.append("--github-action")
        elif args.git_diff:
            test_plan_argv.append("--git-diff")
            test_plan_argv.append(args.git_diff)
        elif args.changed_files:
            test_plan_argv.append("--changed-files")
            test_plan_argv.extend(args.changed_files)
        
        test_plan_argv.append("--format")
        test_plan_argv.append(args.format)
        
        old_argv = sys.argv
        sys.argv = [old_argv[0]] + test_plan_argv
        result = test_plan_main()
        sys.argv = old_argv
        return result
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 