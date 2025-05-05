"""Test the main functionality of the internal tools."""

import pytest
from pathlib import Path

from .utils import Example, ExampleType, get_examples, parse_frontmatter


def test_get_examples():
    """Test that we can find examples in the repository."""
    examples = get_examples()
    assert len(examples) > 0
    
    # Check that we have the hello world example
    hello_world_examples = [e for e in examples if e.repo_filename == "01_getting_started/01_hello_world.py"]
    assert len(hello_world_examples) == 1
    
    # Check that the example is configured correctly
    hello_world = hello_world_examples[0]
    assert hello_world.type == ExampleType.MODULE
    assert "hello_world.py" in hello_world.filename
    assert hello_world.metadata is not None
    assert hello_world.metadata.get("deploy") is True
    assert hello_world.cli_args is not None
    assert "prefect" in hello_world.cli_args[0]
    assert "deployment" in hello_world.cli_args[1]
    assert hello_world.stem == "01_hello_world"


def test_parse_frontmatter():
    """Test parsing frontmatter from a string."""
    content = """---
deploy: true
cmd: ["prefect", "deployment", "build", "test.py:flow_name"]
---
import prefect

# This is a test file
"""
    
    frontmatter, remainder = parse_frontmatter(content)
    
    assert frontmatter is not None
    assert frontmatter["deploy"] is True
    assert frontmatter["cmd"] == ["prefect", "deployment", "build", "test.py:flow_name"]
    assert "import prefect" in remainder
    assert "# This is a test file" in remainder
    
    # Test with no frontmatter
    content = "import prefect\n\n# This is a test file"
    frontmatter, remainder = parse_frontmatter(content)
    
    assert frontmatter is None
    assert remainder == content 