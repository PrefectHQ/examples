"""Test the main functionality of the internal tools."""

import pytest
from pathlib import Path

from ..utils import Example, ExampleType, get_examples, parse_frontmatter


def test_get_examples():
    """Test that we can find examples in the repository."""
    examples = list(get_examples())
    assert len(examples) > 0
    
    # Check that we have the hello world example
    hello_world_examples = [e for e in examples if "01_getting_started/01_hello_world.py" in e.repo_filename]
    assert len(hello_world_examples) > 0, "Hello world example not found"
    
    # Check that the example is configured correctly
    hello_world = hello_world_examples[0]
    assert hello_world.type == ExampleType.MODULE
    assert "hello_world.py" in hello_world.filename
    assert hello_world.metadata is not None
    assert hello_world.cli_args is not None
    assert hello_world.cli_args[0] in ["prefect", "python"]
    assert hello_world.stem == "01_hello_world"


def test_parse_frontmatter():
    """Test that we can parse frontmatter from example files."""
    example_content = """---
deploy: true
tags:
  - flows
  - getting-started
---

import prefect
from prefect import flow

@flow
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
"""
    frontmatter, code = parse_frontmatter(example_content)
    assert frontmatter is not None
    assert frontmatter.get("deploy") is True
    assert "tags" in frontmatter
    assert "flows" in frontmatter["tags"]
    assert "getting-started" in frontmatter["tags"]
    assert "import prefect" in code
    assert "@flow" in code 