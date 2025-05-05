# Prefect Examples Internal Tools

This directory contains a suite of tools for managing, testing, and deploying Prefect example code. Inspired by the internal tools in the [Modal Examples repository](https://github.com/modal-labs/modal-examples), these tools help maintain quality and organization in the example codebase.

## Core Components

1. **Example Discovery and Metadata**
   - `utils.py`: Core utilities for discovering examples and parsing their metadata
   - Examples can include YAML frontmatter with metadata about testing, deployment, etc.

2. **Testing Framework**
   - `examples_test.py`: Pytest-based testing of examples
   - `test_utils.py`: Tests for the utility functions
   - `conftest.py`: Pytest configuration

3. **Deployment Tools**
   - `deploy.py`: Deploy examples marked for deployment
   - Examples with `deploy: true` in frontmatter can be automatically deployed

4. **Execution Tools**
   - `run_example.py`: Run examples individually or randomly

5. **CI/CD Integration**
   - `generate_test_plan.py`: Create test plans based on changed files
   - `github_workflow_example.yml`: Example GitHub Actions workflow

## Example Frontmatter Format

Examples can include frontmatter in YAML format:

```yaml
---
deploy: true  # Whether to deploy this example
cmd: ["prefect", "deployment", "build", "path/to/file.py:flow_name", "-n", "name"]  # Command to run for deployment
description: A description of this example
tags: ["tag1", "tag2"]  # Categorization tags
env:  # Environment variables to set when running
  KEY1: value1
  KEY2: value2
---
```

## Usage

The tools can be run as a Python module:

```bash
# List all examples
python -m internal list

# Run a specific example
python -m internal run-example -e 01_getting_started/01_hello_world.py

# Run a random example
python -m internal run-example -r

# List examples that would be deployed
python -m internal deploy -l

# Deploy a specific example
python -m internal deploy -e 01_getting_started/01_hello_world.py

# Deploy all examples marked for deployment
python -m internal deploy -a
```

## CI/CD Integration

These tools can be integrated into CI/CD pipelines to:

1. Automatically test examples when they change
2. Deploy examples to Prefect when merged
3. Generate documentation from example metadata
4. Verify that all examples work with the latest Prefect version

## Dependencies

See `requirements.txt` for the dependencies needed to run these tools. 