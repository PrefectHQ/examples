import importlib
import json
import pathlib
import sys

import pytest
from .utils import (
    EXAMPLES_ROOT,
    ExampleType,
    get_examples,
    get_examples_json,
    render_example_md,
)

examples = [ex for ex in get_examples() if ex.type == ExampleType.MODULE]
examples = [ex for ex in examples if ex.metadata.get("pytest", True)]
example_ids = [ex.module for ex in examples]


@pytest.fixture(autouse=False)
def add_root_to_syspath(monkeypatch):
    sys.path.append(str(EXAMPLES_ROOT))
    yield
    sys.path.pop()


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_filename(example):
    assert not example.repo_filename.startswith("/")
    assert pathlib.Path(example.repo_filename).exists()


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_import(example, add_root_to_syspath):
    """Test that the example can be imported."""
    if example.module:
        importlib.import_module(example.module)


@pytest.mark.parametrize("example", examples, ids=example_ids)
def test_example_metadata(example):
    """Test that the example metadata is valid."""
    if example.metadata:
        if "deploy" in example.metadata:
            assert isinstance(example.metadata["deploy"], bool)
        
        if "cmd" in example.metadata:
            assert isinstance(example.metadata["cmd"], list)
            
        if "pytest" in example.metadata:
            assert isinstance(example.metadata["pytest"], bool)
            
        if "env" in example.metadata:
            assert isinstance(example.metadata["env"], dict)
            for key, value in example.metadata["env"].items():
                assert isinstance(key, str)
                assert isinstance(value, str)


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