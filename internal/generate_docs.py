#!/usr/bin/env python3
"""
Generate Markdown documentation from example files.

This script converts Python example files to .mdx files for Mintlify documentation.
"""

import sys
import argparse
from pathlib import Path
import re
from itertools import islice

from .utils import get_examples, render_example_md


def generate_docs(output_dir: str, extension: str = ".mdx"):
    """Generate documentation files from examples.

    Args:
        output_dir: Directory where documentation files will be saved
        extension: File extension for documentation files (.md or .mdx)
    """
    # Create output directory if it doesn't exist
    docs_dir = Path(output_dir)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # Get all examples
    examples = get_examples()

    if not examples:
        print("No examples found.")
        return 0

    # Filter out examples from .venv directory and other unwanted paths
    def should_include_example(example):
        unwanted_prefixes = [".venv/", "venv/", "env/", "node_modules/", "archive/"]
        return not any(
            example.repo_filename.startswith(prefix) for prefix in unwanted_prefixes
        )

    examples = [ex for ex in examples if should_include_example(ex)]

    print(f"Processing {len(examples)} examples...")

    # Keep track of organized examples for the index
    example_categories = {}

    generated_count = 0  # track created docs

    # Generate documentation for each example
    for example in examples:
        # Skip draft examples ----------------------------------------------
        # 1. Check structured metadata parsed by jupytext, if present.
        if (
            example.metadata
            and str(example.metadata.get("draft", "")).lower() == "true"
        ):
            print(f"Skipping draft example (metadata): {example.repo_filename}")
            continue

        # 2. Fallback: Scan the raw source for `draft: true`. This covers files
        #    that encode front-matter as comments (`# draft: true`) or classic
        #    YAML blocks (`---\ndraft: true\n---`). We only scan the first ~200
        #    lines for performance – front-matter should always be near the top.
        head = ""
        try:
            with open(example.filename, "r", encoding="utf-8") as src_file:
                head = "".join(list(islice(src_file, 200)))
        except Exception:
            # If reading fails, assume no draft flag
            head = ""

        draft_pattern = re.compile(
            r"^\s*(?:#\s*)?draft\s*:\s*true\b", re.IGNORECASE | re.MULTILINE
        )
        if draft_pattern.search(head):
            print(f"Skipping draft example (file header): {example.repo_filename}")
            continue

        # Passed draft checks → render markdown
        markdown_content = render_example_md(example)

        # Create category from directory structure - handle both 'examples/' and 'curriculum/' prefixes
        parts = example.repo_filename.split("/")

        if len(parts) > 1:
            # Simply use the directory part as the category to maintain folder structure
            category = parts[0]
        else:
            category = "misc"

        # Add to category list
        if category not in example_categories:
            example_categories[category] = []
        example_categories[category].append(example.repo_filename)

        # Flattened directory: save everything directly in docs_dir.
        # Use the original file name (without numeric prefixes) as the mdx filename.
        original_base = Path(parts[-1]).stem
        # Remove leading numeric prefixes like "01_", "002_", etc.
        cleaned_base = re.sub(r"^\d+_", "", original_base)

        doc_filename = docs_dir / f"{cleaned_base}{extension}"

        # Write the file
        with open(doc_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Generated: {doc_filename}")
        generated_count += 1

    # Index generation has been removed per updated requirements. If an index is needed in the
    # future, this block can be re-enabled or replaced with a different implementation.
    print(f"Created {generated_count} documentation files in {docs_dir}")
    return 0


def main():
    """Main entry point for documentation generation."""
    parser = argparse.ArgumentParser(description="Generate documentation from examples")
    parser.add_argument(
        "-o",
        "--output-dir",
        default="docs",
        help="Output directory for documentation files (default: docs)",
    )
    parser.add_argument(
        "-e",
        "--extension",
        default=".mdx",
        choices=[".md", ".mdx"],
        help="File extension for documentation files (default: .mdx)",
    )

    args = parser.parse_args()

    return generate_docs(args.output_dir, args.extension)


if __name__ == "__main__":
    sys.exit(main())
