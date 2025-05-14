# Prefect Examples Internal Tools

This directory contains internal repository and documentation management code for Prefect Examples. It does not contain examples itself, but rather utilities to test, deploy, and maintain the examples.

## Testing Examples

Prefect cares about the correctness of our examples. This directory contains tools to help test our examples to ensure they work correctly.

### Frontmatter

Examples can include a small frontmatter block in YAML format at the top of the file that controls testing and deployment behavior:

```yaml
---
deploy: true
cmd: ["prefect", "deployment", "build", "path/to/file.py:flow_name"]
pytest: true
env:
  VAR_1: value1
  VAR_2: value2
---
```

Fields:

- `deploy`: If `true`, the example should be deployed in CI. Default is `false`.
- `cmd`: The command to run the example for testing. Default is `["prefect", "run", "<filename>"]`.
- `pytest`: If `true`, the example is included in pytest testing. If `false`, it is excluded. Default is `true`.
- `env`: A dictionary of environment variables to include when testing. Default is `{}`.

## Using the Tools

### Running Examples

You can run examples using the `run_example.py` script:

```bash
# List all examples
python -m internal.run_example --list

# Run a specific example by stem name (filename without extension)
python -m internal.run_example --example hello_world

# Run a specific example by path
python -m internal.run_example --example 01_getting_started/hello_world

# Run a random example
python -m internal.run_example --random
```

### Testing Examples

You can run tests for all examples using pytest:

```bash
pytest -xvs internal/examples_test.py
```

This will:
1. Verify all examples can be found and imported
2. Check that examples can be rendered as markdown
3. Ensure that example metadata is valid

## Example Requirements

For an example to work well with these tools:

1. It should be a well-formed Python file that can be imported without errors
2. If it requires special setup or environment variables, these should be documented in the frontmatter
3. For deployment, it should include a flow that can be deployed with Prefect 