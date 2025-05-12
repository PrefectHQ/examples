import importlib
import json
import pathlib
import pytest
import re
import sys
from typing import List

from ..utils import (
    EXAMPLES_ROOT,
    Example,
    ExampleType,
    get_examples,
    get_examples_json,
)

examples = list(get_examples())
example_ids = [e.repo_filename for e in examples]


@pytest.fixture
def add_root_to_syspath():
    """Add EXAMPLES_ROOT to sys.path."""
    sys.path.insert(0, str(EXAMPLES_ROOT))
    yield
    sys.path.pop(0)


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_filename(example):
    assert not example.repo_filename.startswith("/")
    assert pathlib.Path(example.repo_filename).exists()


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_import(example, add_root_to_syspath):
    """Test that the example can be imported."""
    if example.module:
        # Extract the module path relative to examples directory
        module_path = example.module
        if module_path.startswith("examples."):
            module_path = module_path[len("examples."):]
        importlib.import_module(module_path)


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_example_metadata(example):
    """Test that example metadata is valid."""
    # Repo filename should be a valid relative path
    assert not example.repo_filename.startswith("/")
    assert pathlib.Path(example.repo_filename).exists()
    
    # Each example should have metadata
    assert example.metadata is not None
    
    # If deploy is True, the example should have a cmd
    if example.metadata.get("deploy", False):
        assert example.cli_args is not None
        assert len(example.cli_args) > 0
        assert example.cli_args[0] in ["prefect", "python"]


def test_get_examples_json():
    """Test that get_examples_json returns valid JSON."""
    examples_json = get_examples_json()
    assert isinstance(examples_json, str)
    
    # Should be parseable as JSON
    examples_list = json.loads(examples_json)
    assert isinstance(examples_list, list)
    
    # Each example should have required fields
    for example in examples_list:
        assert "filename" in example
        assert "repo_filename" in example
        
        if "metadata" in example:
            assert isinstance(example["metadata"], dict) 