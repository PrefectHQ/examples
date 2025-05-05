import json
import re
import yaml
import os
import subprocess
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Iterator

EXAMPLES_ROOT = Path(__file__).parent.parent


class ExampleType(Enum):
    MODULE = 1
    ASSET = 2


@dataclass
class Example:
    type: ExampleType
    filename: str  # absolute filepath to example file
    module: Optional[str] = None  # python import path, or None if file is not a py module
    metadata: Optional[Dict[str, Any]] = None
    repo_filename: str = ""  # git repo relative filepath
    cli_args: Optional[List[str]] = None  # Full command line args to run it
    stem: Optional[str] = None  # stem of path
    tags: Optional[List[str]] = field(default_factory=list)  # metadata tags for the example
    env: Optional[Dict[str, str]] = None  # environment variables

    def dict(self):
        """Convert to dict for JSON serialization."""
        result = asdict(self)
        # Convert ExampleType to int for JSON serialization
        result["type"] = result["type"].value
        return result


def parse_frontmatter(content: str) -> Tuple[Optional[Dict[str, Any]], str]:
    """Parse YAML frontmatter from a string.
    
    Returns a tuple of (frontmatter, remaining_content).
    If no frontmatter is found, returns (None, content).
    """
    # Check if the file starts with '---' (frontmatter delimiter)
    if not content.startswith("---"):
        return None, content
    
    # Find the end of the frontmatter
    end_delim = content.find("---", 3)
    if end_delim == -1:
        return None, content
    
    # Extract the frontmatter
    frontmatter_str = content[3:end_delim].strip()
    remaining_content = content[end_delim + 3:].strip()
    
    try:
        frontmatter = yaml.safe_load(frontmatter_str)
        if not isinstance(frontmatter, dict):
            return None, content
        return frontmatter, remaining_content
    except yaml.YAMLError:
        return None, content


def render_example_md(example: Example) -> str:
    """Render an example as markdown."""
    with open(example.filename, "r") as f:
        content = f.read()
    
    # Skip frontmatter for rendering
    _, content = parse_frontmatter(content)
    
    result = f"# {os.path.basename(example.repo_filename)}\n\n"
    
    if example.metadata and "description" in example.metadata:
        result += f"{example.metadata['description']}\n\n"
    
    result += "```python\n"
    result += content
    result += "\n```\n"
    
    return result


def get_example_files() -> Iterator[Path]:
    """Get all Python files in the repository."""
    for path in EXAMPLES_ROOT.glob("**/*.py"):
        if ".git" in path.parts:
            continue
        
        # Skip tests and setup files
        if (
            path.name.startswith("test_")
            or path.name.startswith("conftest.py")
            or "setup.py" in path.name
        ):
            continue
        
        # Skip internal tools
        if "internal" in path.parts:
            continue
        
        yield path


def get_repo_relative_path(path: Path) -> str:
    """Get the path relative to the repository root."""
    return str(path.relative_to(EXAMPLES_ROOT))


def get_import_module(file_path: Path) -> Optional[str]:
    """Get the import module for a Python file."""
    rel_path = file_path.relative_to(EXAMPLES_ROOT)
    
    if "__init__.py" in str(rel_path):
        # For __init__.py files, the module is the parent directory
        return str(rel_path.parent).replace("/", ".")
    
    # For regular Python files, the module is the file without .py
    module = str(rel_path.with_suffix("")).replace("/", ".")
    return module


def parse_metadata_and_get_cli_args(file_path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[List[str]]]:
    """Parse metadata and get CLI args for an example."""
    with open(file_path, "r") as f:
        content = f.read()
    
    metadata, _ = parse_frontmatter(content)
    
    cli_args = None
    if metadata and "cmd" in metadata:
        cli_args = metadata["cmd"]
    else:
        # Default to running the script with python
        cli_args = ["python", str(file_path)]
    
    return metadata, cli_args


def get_examples() -> List[Example]:
    """Get all examples in the repository."""
    examples = []
    
    for file_path in get_example_files():
        file_type = ExampleType.MODULE
        repo_rel_path = get_repo_relative_path(file_path)
        abs_path = str(file_path.absolute())
        
        metadata, cli_args = parse_metadata_and_get_cli_args(file_path)
        
        examples.append(
            Example(
                type=file_type,
                filename=abs_path,
                module=get_import_module(file_path),
                metadata=metadata,
                repo_filename=repo_rel_path,
                cli_args=cli_args,
                stem=file_path.stem,
                env=metadata.get("env") if metadata else None,
            )
        )
    
    return examples


def get_examples_json() -> str:
    """Get examples as JSON string."""
    examples = get_examples()
    examples_dicts = [e.dict() for e in examples]
    return json.dumps(examples_dicts, indent=2) 