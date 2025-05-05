# Prefect Examples

This repository contains a collection of examples demonstrating how to use [Prefect](https://www.prefect.io/), the workflow orchestration tool for data engineers and data scientists.

## Repository Structure

```
prefect-examples/
├── 01_getting_started/    # Basic examples to get started with Prefect
├── 02_sdk_concepts/       # Examples showcasing core Prefect SDK features
├── internal/              # Internal tools for testing, documentation, and deployment
├── scripts/               # Helper scripts for local testing and development
└── docs/                  # Generated documentation files (when created)
```

## Example Format

Each example in this repository follows a consistent format using YAML frontmatter to provide metadata:

```python
---
deploy: true                                          # Whether this example should be deployed
cmd: ["prefect", "deployment", "build", "file:flow"]  # Command to deploy this example
description: A short description of the example        # Description for documentation
tags: ["tag1", "tag2"]                                # Categorization tags
---
# Python code follows...
```

## Running Examples

To run an individual example:

```bash
python 01_getting_started/01_hello_world.py
```

You can also use the internal tooling to run examples:

```bash
# List all examples
python -m internal list

# Run a specific example
python -m internal run-example -e 01_getting_started/01_hello_world.py

# Run a random example
python -m internal run-example -r
```

## Automated Testing

This repository includes a GitHub Actions workflow that automatically tests examples when they change:

1. When a pull request is created or updated, the workflow runs
2. It identifies which Python files have changed
3. It runs each changed example to ensure it works properly
4. It reports pass/fail status for each example

This ensures that all examples in the repository are valid and working before they're published to documentation.

### Local Testing

You can test examples locally using the scripts in the `scripts/` directory:

```bash
# Test examples changed in the most recent commit
./scripts/test-locally.sh

# Test specific examples (edit the script to specify which ones)
./scripts/test-specific.sh
```

## Documentation Generation

This repository includes tooling to automatically generate Markdown documentation (.mdx files) from the Python examples for use with Mintlify, Prefect's documentation platform.

### Generating Documentation Locally

To generate documentation:

```bash
# Generate .mdx files in the 'docs' directory
python -m internal generate-docs

# Specify a different output directory
python -m internal generate-docs -o custom_docs

# Use .md extension instead of .mdx
python -m internal generate-docs -e .md
```

The generated documentation will include:
- Files organized by category (based on directory structure)
- An index file with links to all examples
- Proper formatting of code with syntax highlighting
- Inclusion of metadata from frontmatter

### Automated Documentation Deployment

This repository is configured with a GitHub Actions workflow that automatically:

1. Generates documentation from examples
2. Creates a pull request to the main [Prefect repository](https://github.com/PrefectHQ/prefect) in the `docs/v3/examples` directory

For more details about this process, see [DOCS_DEPLOYMENT.md](DOCS_DEPLOYMENT.md).

## Deploying Examples

Examples marked with `deploy: true` in their frontmatter can be deployed to a Prefect server:

```bash
# List examples that would be deployed
python -m internal deploy -l

# Deploy a specific example
python -m internal deploy -e 01_getting_started/01_hello_world.py

# Deploy all examples marked for deployment
python -m internal deploy -a
```

## Development

### Requirements

- Python 3.10 or later
- Dependencies in `internal/requirements.txt`

### Setting Up

```bash
# Clone the repository
git clone https://github.com/yourusername/prefect-examples.git
cd prefect-examples

# Install dependencies
pip install -r internal/requirements.txt
```

### Contributing New Examples

1. Create a new Python file in the appropriate directory
2. Add frontmatter metadata at the top of the file
3. Implement your Prefect flow with clear comments
4. Run `python -m internal list` to verify your example is discovered
5. Run `python -m internal generate-docs` to preview documentation
6. Test your example with `./scripts/test-specific.sh` (after adding it to the script)

### CI/CD Workflows

The repository uses GitHub Actions for continuous integration and deployment:

- `.github/workflows/test-examples.yml`: Tests examples when they change in a PR
- `.github/workflows/docs-deploy.yml`: Generates and deploys documentation to the Prefect repository

### Internal Tools

The `internal/` directory contains various tools for maintaining this repository:

- **utils.py**: Core utilities for discovering and parsing examples
- **run_example.py**: Tools for running examples
- **deploy.py**: Tools for deploying examples
- **examples_test.py**: Pytest-based testing of examples
- **generate_docs.py**: Documentation generation
- **generate_test_plan.py**: Tools for CI/CD testing
