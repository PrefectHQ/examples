"""Tests for the utils module."""

import pytest
from pathlib import Path

from ..utils import (
    EXAMPLES_ROOT,
    Example,
    ExampleType,
    parse_frontmatter,
    render_example_md,
    get_example_files,
    get_examples,
    get_examples_json,
)


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


def test_parse_frontmatter_no_frontmatter():
    """Test parsing a string with no frontmatter."""
    content = """import prefect

# This is a test file
"""
    frontmatter, remainder = parse_frontmatter(content)
    
    assert frontmatter is None
    assert remainder == content


def test_get_example_files():
    """Test getting example files from the repository."""
    files = get_example_files()
    
    assert len(files) > 0
    assert all(f.is_file() for f in files)
    assert all(f.suffix == ".py" for f in files)
    assert all(not str(f).startswith("internal/") for f in files)


def test_get_examples():
    """Test getting examples from the repository."""
    examples = get_examples()
    
    assert len(examples) > 0
    assert all(isinstance(e, Example) for e in examples)
    assert all(e.type == ExampleType.MODULE for e in examples)
    assert all(Path(e.filename).exists() for e in examples)


def test_get_examples_json():
    """Test getting examples as JSON."""
    json_str = get_examples_json()
    
    assert isinstance(json_str, str)
    assert json_str.startswith("[")
    assert json_str.endswith("]")
    
    import json
    examples = json.loads(json_str)
    assert len(examples) > 0
    assert all("filename" in e for e in examples)
    assert all("repo_filename" in e for e in examples) 