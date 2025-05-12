# Testing Scripts

This directory contains scripts for testing Prefect examples.

## Available Scripts

### test-locally.sh

Tests examples that have changed in the most recent commit:

```bash
# Run with dependency installation (default)
./scripts/test-locally.sh

# Skip dependency installation 
./scripts/test-locally.sh --skip-install
```

This is useful for verifying your changes before committing or pushing.

### test-specific.sh

Tests specific examples you define in the script:

```bash
# Run without installing dependencies
./scripts/test-specific.sh

# Install dependencies before running
./scripts/test-specific.sh --install
```

Edit the `CHANGED_FILES` variable at the top of the script to specify which example files to test.

## Package Installation

Both scripts will use `uv` (a faster Python package installer) if it's available on your system, with a fallback to traditional `pip` if:
- `uv` isn't found on your system
- `uv` fails to build a package (common with packages that have native extensions)

To install uv:

```bash
pip install uv
```

## How the Testing Works

Both scripts:

1. Install dependencies (if requested)
2. Generate a test plan based on the specified files
3. Create temporary versions of each example with the frontmatter removed
4. Run each example to verify it works
5. Report which examples passed or failed

This mimics how examples are tested in the GitHub Actions workflow. 