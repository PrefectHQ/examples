import json
import re
import warnings
from enum import Enum
from pathlib import Path
from typing import Iterator, Optional, Tuple

from pydantic import BaseModel

EXAMPLES_ROOT = Path(__file__).parent.parent


with warnings.catch_warnings():
    # This triggers some dumb warning in jupyter_core
    warnings.simplefilter("ignore")
    import jupytext
    import jupytext.config


class ExampleType(int, Enum):
    MODULE = 1
    ASSET = 2


class Example(BaseModel):
    type: ExampleType
    filename: str  # absolute filepath to example file
    module: Optional[str] = (
        None  # python import path, or none if file is not a py module.
    )
    # TODO(erikbern): don't think the module is used (by docs or monitors)?
    metadata: Optional[dict] = None
    repo_filename: str  # git repo relative filepath
    cli_args: Optional[list] = None  # Full command line args to run it
    stem: Optional[str] = None  # stem of path
    tags: Optional[list[str]] = None  # metadata tags for the example
    env: Optional[dict[str, str]] = None  # environment variables for the example


_RE_NEWLINE = re.compile(r"\r?\n")
_RE_FRONTMATTER = re.compile(r"^---$", re.MULTILINE)
_RE_CODEBLOCK = re.compile(r"\s*```[^`]+```\s*", re.MULTILINE)


def render_example_md(example: Example) -> str:
    """Render a Python code example to Markdown documentation format."""

    with open(example.filename, encoding="utf-8") as f:
        content = f.read()

    lines = _RE_NEWLINE.split(content)
    markdown: list[str] = []
    code: list[str] = []
    for line in lines:
        if line == "#" or line.startswith("# "):
            if code:
                markdown.extend(["```python", *code, "```", ""])
                code = []
            markdown.append(line[2:])
        else:
            if markdown and markdown[-1]:
                markdown.append("")
            if code or line:
                code.append(line)

    if code:
        markdown.extend(["```python", *code, "```", ""])

    text = "\n".join(markdown)
    if _RE_FRONTMATTER.match(text):
        # Strip out frontmatter from text.
        if match := _RE_FRONTMATTER.search(text, 4):
            github_base_url = "https://github.com/prefecthq/examples/blob/examples-markdown/examples/"
            github_url = f"{github_base_url}{example.repo_filename}"

            # Using raw HTML for precise placement; most Markdown/MDX renderers will
            # preserve the styling while allowing fallback to a plain link if HTML
            # is stripped.
            github_button = (
                f'<a href="{github_url}" target="_blank">View on GitHub</a>\n\n'
            )

            frontmatter = "---\n"

            for line in text[:match.end()].split("\n"):
                if line.startswith(("title:", "description:")):
                    frontmatter += line + "\n"

            frontmatter += "---\n\n"

            # Insert the button at the very top of the document.
            text = frontmatter + github_button + text[match.end() + 1 :]

    if match := _RE_CODEBLOCK.match(text):
        filename = Path(example.filename).name
        if match.end() == len(text):
            # Special case: The entire page is a single big code block.
            text = f"""# Example ({filename})

This is the source code for **{example.module}**.
{text}"""

    return text


def gather_example_files(
    parents: list[str], subdir: Path, ignored: list[str], recurse: bool
) -> Iterator[Example]:
    config = jupytext.config.JupytextConfiguration(
        root_level_metadata_as_raw_cell=False
    )

    for filename in sorted(list(subdir.iterdir())):
        if filename.is_dir() and recurse:
            # Gather two-subdirectories deep, but no further.
            yield from gather_example_files(
                parents + [str(subdir.stem)], filename, ignored, recurse=False
            )
        else:
            filename_abs: str = str(filename.resolve())
            ext: str = filename.suffix
            if parents:
                repo_filename: str = (
                    f"{'/'.join(parents)}/{subdir.name}/{filename.name}"
                )
            else:
                repo_filename: str = f"{subdir.name}/{filename.name}"

            if ext == ".py" and filename.stem != "__init__":
                if parents:
                    parent_mods = ".".join(parents)
                    module = f"examples.{parent_mods}.{subdir.stem}.{filename.stem}"
                else:
                    module = f"examples.{subdir.stem}.{filename.stem}"
                data = jupytext.read(open(filename_abs, encoding="utf-8"), config=config)
                metadata = data["metadata"]["jupytext"].get("root_level_metadata", {})
                cmd = metadata.get("cmd", ["prefect", "run", repo_filename])
                args = metadata.get("args", [])
                tags = metadata.get("tags", [])
                env = metadata.get("env", dict())
                yield Example(
                    type=ExampleType.MODULE,
                    filename=filename_abs,
                    metadata=metadata,
                    module=module,
                    repo_filename=repo_filename,
                    cli_args=(cmd + args),
                    stem=Path(filename_abs).stem,
                    tags=tags,
                    env=env,
                )
            elif ext in [".png", ".jpeg", ".jpg", ".gif", ".mp4"]:
                yield Example(
                    type=ExampleType.ASSET,
                    filename=filename_abs,
                    repo_filename=repo_filename,
                )
            else:
                ignored.append(str(filename))


def get_examples() -> Iterator[Example]:
    """Yield all Python module files and asset files relevant to building docs"""
    # Process examples directory
    examples_dir = EXAMPLES_ROOT / "examples"
    if not examples_dir.exists():
        raise Exception(
            f"Can't find directory {examples_dir}. You might need to clone the examples repo there."
        )

    ignored = []
    for subdir in sorted(
        p
        for p in examples_dir.iterdir()
        if p.is_dir()
        and not p.name.startswith(".")
        and not p.name.startswith("internal")
        and not p.name.startswith("misc")
    ):
        yield from gather_example_files(
            parents=[], subdir=subdir, ignored=ignored, recurse=True
        )

    # Process PACC directory
    pacc_dir = EXAMPLES_ROOT / "pacc"
    if pacc_dir.exists():
        # Handle subdirectories
        for subdir in sorted(
            p
            for p in pacc_dir.iterdir()
            if p.is_dir()
            and not p.name.startswith(".")
            and not p.name.startswith("internal")
            and not p.name.startswith("misc")
        ):
            yield from gather_example_files(
                parents=[], subdir=subdir, ignored=ignored, recurse=True
            )

        # Handle Python files directly in PACC directory
        for file in sorted(
            p
            for p in pacc_dir.iterdir()
            if p.is_file() and p.suffix == ".py" and p.name != "__init__.py"
        ):
            filename_abs = str(file.resolve())
            repo_filename = f"pacc/{file.name}"
            module = f"pacc.{file.stem}"

            config = jupytext.config.JupytextConfiguration(
                root_level_metadata_as_raw_cell=False
            )

            try:
                data = jupytext.read(open(filename_abs, encoding="utf-8"), config=config)
                metadata = data["metadata"]["jupytext"].get("root_level_metadata", {})
            except Exception:
                metadata = {}

            cmd = metadata.get("cmd", ["prefect", "run", repo_filename])
            args = metadata.get("args", [])
            tags = metadata.get("tags", [])
            env = metadata.get("env", dict())

            yield Example(
                type=ExampleType.MODULE,
                filename=filename_abs,
                metadata=metadata,
                module=module,
                repo_filename=repo_filename,
                cli_args=(cmd + args),
                stem=file.stem,
                tags=tags,
                env=env,
            )


def get_examples_json():
    examples = list(ex.dict() for ex in get_examples())
    return json.dumps(examples)


# ---------------------------------------------------------------------------
# Frontmatter parsing -------------------------------------------------------
# ---------------------------------------------------------------------------


def parse_frontmatter(content: str) -> Tuple[Optional[dict], str]:
    """Extract YAML front-matter from a file and return (metadata, code).

    If no front-matter block (bounded by `---` lines) is found, returns
    ``(None, content)``.
    """

    frontmatter_pattern = re.compile(r"^---\s*$([\s\S]*?)^---\s*$", re.MULTILINE)
    match = frontmatter_pattern.search(content)

    if not match:
        return None, content

    # Attempt to parse YAML safely, but fallback to an empty dict on error to
    # avoid introducing a runtime dependency (PyYAML).
    yaml_text = match.group(1)
    try:
        import yaml  # optional dependency

        metadata = yaml.safe_load(yaml_text) or {}
    except Exception:
        metadata = {}

    cleaned_content = content[: match.start()] + content[match.end() :]
    return metadata, cleaned_content.strip()


if __name__ == "__main__":
    for example in get_examples():
        print(example.json())