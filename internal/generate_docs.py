#!/usr/bin/env python3
"""
Generate Markdown documentation from example files.

This script converts Python example files to .mdx files for Mintlify documentation.
"""

import os
import sys
import argparse
from pathlib import Path
import re

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
        unwanted_prefixes = [
            '.venv/',
            'venv/',
            'env/',
            'node_modules/'        ]
        return not any(example.repo_filename.startswith(prefix) for prefix in unwanted_prefixes)
    
    examples = [ex for ex in examples if should_include_example(ex)]
    
    print(f"Processing {len(examples)} examples...")
    
    # Keep track of organized examples
    example_categories = {}
    
    # Generate documentation for each example
    for example in examples:
        # Get markdown content
        markdown_content = render_example_md(example)
        
        # Create category from directory structure - handle both 'examples/' and 'curriculum/' prefixes
        parts = example.repo_filename.split('/')
        
        if len(parts) > 1:
            # Simply use the directory part as the category to maintain folder structure
            category = parts[0]
        else:
            category = "misc"
        
        # Add to category list
        if category not in example_categories:
            example_categories[category] = []
        example_categories[category].append(example.repo_filename)
        
        # Create directory structure in docs dir if needed
        category_dir = docs_dir / category
        category_dir.mkdir(exist_ok=True)
        
        # Create filename (extract the stem of the last part of the path)
        base_filename = Path(parts[-1]).stem
        doc_filename = category_dir / f"{base_filename}{extension}"
        
        # Write the file
        with open(doc_filename, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        
        print(f"Generated: {doc_filename}")
    
    # Create an index file
    index_path = docs_dir / f"index{extension}"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write("# Prefect Examples\n\n")
        f.write("This documentation is auto-generated from the Prefect Examples repository.\n\n")
        
        for category, examples in sorted(example_categories.items()):
            # Clean up category name for display - remove numeric prefixes like "01_", "02_", etc.
            display_category = re.sub(r'^\d+_', '', category).replace('_', ' ').title()
            f.write(f"## {display_category}\n\n")
            
            for example in sorted(examples):
                # Create a nice name and link
                parts = example.split('/')
                base_name = Path(parts[-1]).stem
                display_name = base_name.replace('_', ' ').title()
                
                # Create relative link based on the directory structure
                if parts[0] == 'examples' and len(parts) > 2:
                    # For examples directory, use the subdirectory as the category
                    category_part = parts[1]
                    link_path = f"{category_part}/{Path(parts[-1]).stem}{extension}"
                elif parts[0] == 'curriculum':
                    # For curriculum directory, use 'curriculum' as the category
                    link_path = f"curriculum/{Path(parts[-1]).stem}{extension}"
                elif parts[0] == 'pacc':
                    # For PACC directory, use 'pacc' as the category
                    link_path = f"pacc/{Path(parts[-1]).stem}{extension}"
                else:
                    link_path = f"{category}/{Path(parts[-1]).stem}{extension}"
                
                f.write(f"- [{display_name}]({link_path})\n")
            
            f.write("\n")
    
    print(f"Generated index: {index_path}")
    print(f"Created {len(examples)} documentation files in {docs_dir}")
    return 0

def main():
    """Main entry point for documentation generation."""
    parser = argparse.ArgumentParser(description="Generate documentation from examples")
    parser.add_argument(
        "-o", "--output-dir",
        default="docs",
        help="Output directory for documentation files (default: docs)"
    )
    parser.add_argument(
        "-e", "--extension",
        default=".mdx",
        choices=[".md", ".mdx"],
        help="File extension for documentation files (default: .mdx)"
    )
    
    args = parser.parse_args()
    
    return generate_docs(args.output_dir, args.extension)

if __name__ == "__main__":
    sys.exit(main()) 