# Prefect Examples

A collection of opinionated examples and guided learning paths demonstrating how to use [Prefect](https://www.prefect.io/), the only workflow orchestration tool for data engineers and data scientists.

## Overview

This repository contains narrative-driven, opinionated examples that showcase Prefect's core features and capabilities. Each example is designed not just to demonstrate functionality, but to tell a story about the benefits of leveraging Prefect in data engineering workflows. Whether you're just getting started with Prefect or looking to implement advanced patterns, you'll find useful code samples and best practices here.

## Repository Structure

> **In transition.** This repo is becoming the single home for Prefect, Dagster and FastMCP examples. New examples go in the product folders below and follow the [example contract](internal/example-contract.md); every one is listed in [`CATALOG.yaml`](CATALOG.yaml). Existing Prefect examples move into `prefect/` in a later phase. Some files are loaded by other repos from `main` and must not move yet; see [`internal/DOWNSTREAM.md`](internal/DOWNSTREAM.md).
>
> - **prefect/**, **dagster/**, **fastmcp/** – Examples for each product
> - **stacks/** – Examples that combine products
> - **learn/** – Guided curricula
> - **demos/** – Frozen talk, workshop and SE demos, kept out of the docs

The current layout:

- **examples/** – Narrative-driven Python examples grouped by topic  
  - **01_getting_started/** – First steps with Prefect  
  - **02_flows/** – Deeper exploration of various flow scenarios 
  - **archive/** – Various stand-alone Prefect flows ready to copy-paste into projects

- **pal/** – The *Prefect Accelerated Learning* curriculum, a step-by-step learning path  

- **flows/** – Stand-alone Prefect flow scripts ready to copy-paste into projects  

- **apps/** – End-to-end reference applications that orchestrate background tasks with Prefect  

- **scripts/** – Utility scripts for interacting with Prefect Cloud or the API  

- **internal/** – Tooling to test, lint, and convert examples into documentation  

- **docs/** – Auto-generated MDX documentation built from example Python files  

## Documentation Generation

All examples are written as Python files with detailed comments that explain concepts alongside runnable code. These files are then automatically converted to MDX documentation:

```bash
# Generate .mdx docs
uv run generate-docs  # defaults to /docs
# or
# create them locally for testing purposes
python -m internal generate-docs -o temp/docs -e .mdx
```

This process preserves both the narrative explanations and executable code, making the examples both readable as documentation and runnable as demonstrations.

## Getting Started

### Prerequisites

- Python 3.13+
- [Prefect](https://docs.prefect.io/) 3.3.5+

### Installation

```bash
# Clone the repository
git clone https://github.com/PrefectHQ/examples.git
cd examples

# Create (or re-use) a local virtual environment with uv
uv venv               # creates .venv in the current directory
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
# List all available examples
python -m internal run-example -l

# Run a specific example by repository path
python -m internal run-example -e 01_getting_started/01_hello_world.py
```

## Example Format

Each example includes:

1. A descriptive header with metadata in YAML frontmatter
2. Detailed narrative comments explaining concepts, use cases, and benefits
3. Runnable code that demonstrates Prefect features
4. "What Just Happened?" sections that walk through execution steps
5. Real-world context explaining why features matter in production environments

Examples follow a consistent structure based on templates in the `internal/templates` directory that ensures comprehensive coverage of each feature.

## How to Contribute 🛠

We love contributions!  Follow the steps below to add a new example.

1. **Fork & branch**

   ```bash
   git checkout -b my-new-example
   ```

2. **Start from a template**

   Copy one of the files in `internal/templates/` (e.g. `feature.py` or `scenario.py`) and rename it to something meaningful inside the appropriate folder (`examples/`). Or use them as context for an llm driven tool. Please keep each pull-request limited to **one new file** so that reviews stay focused. 

3. **Tell the story**

   Fill in the template:
   - Add YAML front-matter (`title`, `description`, etc.).
   - Use narrative comments (`#`) to explain the *why* as well as the *how*.
   - Include runnable code blocks that a reader can copy & paste.

4. **Verify locally**
a. Test your code:
    ```
    python -m internal run-example -e example_module/your_new_example.py
    ```
    b. Build the documentation for just-added file:
    ```
   uv run generate-docs  # defaults to /docs
   ```
   or
   ```
   python -m internal generate-docs -o temp/docs -e .mdx
   ```

   c. Open temp/docs/<path-to-your-file>.mdx in a browser or editor
   

5. **Open a pull-request**

   Push your branch and open a PR.  GitHub Actions will rerun tests and rebuild docs to make sure everything still passes.

6. **Celebrate 🎉**

   Once the PR is merged, your example will automatically appear in the next docs build.

For larger changes, open an issue first so we can discuss the design before you start coding.
