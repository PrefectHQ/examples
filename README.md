# Prefect Examples

A collection of opinionated examples and guided learning paths demonstrating how to use [Prefect](https://www.prefect.io/), the only workflow orchestration tool for data engineers and data scientists.

## Overview

This repository contains narrative-driven, opinionated examples that showcase Prefect's core features and capabilities. Each example is designed not just to demonstrate functionality, but to tell a story about the benefits of leveraging Prefect in data engineering workflows. Whether you're just getting started with Prefect or looking to implement advanced patterns, you'll find useful code samples and best practices here.

## Repository Structure

- **examples/**: The main examples directory, organized by topic:
  - **01_getting_started/**: Basic concepts and first steps with Prefect
  - **02_sdk_concepts/**: Deeper exploration of Prefect's Python SDK
  - **03_cloud_concepts/**: Features related to Prefect Cloud and remote execution

- **pacc/**: (Prefect Accelerator) A guided learning curriculum with structured learning paths progressing from fundamentals to advanced topics:
  - Organized in sequential phases (01-07) covering foundations to advanced integrations
  - Each module builds on previous knowledge and points to relevant examples

- **docs/**: Generated MDX documentation files converted from Python examples
  - Contains the same examples and learning paths but in a format readable by MDSvex

- **internal/**: Tools for testing, deploying, and maintaining the examples
  - Includes templates and utilities for converting Python files to MDX documentation

- **tests/**: Test suite to ensure examples work correctly

## Documentation Generation

All examples are written as Python files with detailed comments that explain concepts alongside runnable code. These files are then automatically converted to MDX documentation:

```bash
python -m internal.generate_docs -o docs
```

This process preserves both the narrative explanations and executable code, making the examples both readable as documentation and runnable as demonstrations.

## Getting Started

### Prerequisites

- Python 3.13+
- [Prefect](https://docs.prefect.io/) 3.3.5+

### Installation

```bash
# Clone the repository
git clone https://github.com/PrefectHQ/prefect-examples.git
cd prefect-examples

# Set up a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies using UV
uv pip install -e .
```

### Running Examples

You can run examples directly:

```bash
python examples/01_getting_started/01_hello_world.py
```

Or use the included utility script:

```bash
# List all examples
python -m internal.run_example --list

# Run a specific example by name
python -m internal.run_example --example hello_world

# Run a random example
python -m internal.run_example --random
```

## Example Format

Each example includes:

1. A descriptive header with metadata in YAML frontmatter
2. Detailed narrative comments explaining concepts, use cases, and benefits
3. Runnable code that demonstrates Prefect features
4. "What Just Happened?" sections that walk through execution steps
5. Real-world context explaining why features matter in production environments

Examples follow a consistent structure based on templates in the `internal/templates` directory that ensures comprehensive coverage of each feature.

## Contributing

Contributions to improve existing examples or add new ones are welcome! Please see the contributing guidelines for more information and refer to the template in `internal/templates/TEMPLATE_README.md` when creating new examples.
