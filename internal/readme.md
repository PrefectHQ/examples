# Prefect Examples Internal Tools

This directory contains internal repository and documentation management code for Prefect Examples. It does not contain examples itself, but rather utilities to test, deploy, and maintain the examples.

## Testing Examples

Prefect cares about the correctness of our examples. This directory contains tools to help test our examples to ensure they work correctly.

### Frontmatter

Examples can include a small frontmatter block in YAML format at the top of the file that controls testing, documentation, and deployment behavior:

```yaml
---
# Display information used by the docs generator
title: Hello, world!
description: Your first steps with Prefect.

# CI / deployment controls
deploy: true                    # Deploy this example in CI (default: false)
pytest: true                    # Include in pytest test suite (default: true)

# How to execute this example
cmd:  ["prefect", "run", "path/to/file.py"]   # Base command to run (default shown)
args: ["--param", "value"]                     # Extra CLI args appended after cmd

# Supplementary metadata
dependencies: ["prefect"]      # Packages required by the example
env:
  VAR_1: value1                 # Environment variables set when running
  VAR_2: value2

# Optional categorisation
tags: [getting_started, flows]
---
```

Fields:
- `title`: A human-readable title for documentation; optional.
- `description`: A short description used in the docs; optional.
- `pytest`: If `true`, the example is included in pytest testing. If `false`, it is excluded. Default is `true`.
- `cmd`: The base command used to run the example. Default is `["prefect", "run", "<filename>"]`.
- `args`: A list of additional CLI arguments appended to `cmd`. Default is `[]`.
- `env`: A dictionary of environment variables available when the example is executed. Default is `{}`.
- `tags`: A list of tags used for categorising and filtering examples. Default is `[]`.
- `dependencies`: Extra Python dependencies required by the example. These will be installed in CI if needed.

## Using the Tools

### Running Examples

The preferred entry-point for all internal utilities is the `internal` module. Use the `run-example` sub-command to execute examples:

```bash
# List all available examples
python -m internal run-example -l

# Run a specific example by repository path
python -m internal run-example -e 01_getting_started/01_hello_world.py

# Run a specific example by stem name (filename without extension)
python -m internal run-example -e hello_world

# Run a random example
python -m internal run-example -r
```

You can also list examples without the `run-example` command:

```bash
python -m internal list
```

### Testing Examples

Run the full test-suite with pytest:

```bash
pytest -xvs internal/tests
```

This will:
1. Verify all examples can be discovered and imported
2. Check that examples can be rendered as markdown
3. Ensure that example metadata is valid

### Documentation Generation

You can convert example files to Markdown / MDX documentation:

```bash
# Generate documentation into a temporary directory for local testing
python -m internal generate-docs -o temp/docs -e .mdx
# or
uv run generate-docs  # defaults to /docs
```

The `temp/docs/` directory is ignored by Git (see `.gitignore`) so you can iterate on documentation locally without affecting the `docs/` folder that is built in CI.

### Test-plan Utility

Generate a test plan for changed files (useful in CI):

```bash
python -m internal test-plan --github-action --format json
```

## Example Requirements

For an example to work well with these tools:

1. It should be a well-formed Python file that can be imported without errors.
2. If it requires special setup or environment variables, these should be documented in the frontmatter.
3. For deployment, it should include a flow that can be deployed with Prefect. 