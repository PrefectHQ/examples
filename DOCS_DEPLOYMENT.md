# Documentation Deployment

This repository contains a GitHub Actions workflow that automatically generates documentation from example files and creates a pull request to the main Prefect repository.

## Setup Instructions

To enable the automatic documentation deployment, you need to set up a GitHub Personal Access Token (PAT) with the appropriate permissions.

### Create a GitHub Personal Access Token (PAT)

1. Go to your GitHub Settings → [Developer settings](https://github.com/settings/tokens) → Personal access tokens
2. Click "Generate new token" (classic)
3. Give it a name, e.g., "Prefect Examples Documentation Deployment"
4. Set an expiration date (or "No expiration" if appropriate)
5. Select the following scopes:
   - `repo` (Full control of private repositories)
6. Click "Generate token"
7. **Copy the token immediately** (you won't be able to see it again)

### Add the Token to Your Repository Secrets

1. Go to your repository settings
2. Navigate to "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Name: `GH_PAT`
5. Value: Paste the token you copied
6. Click "Add secret"

## How It Works

The workflow is defined in `.github/workflows/docs-deploy.yml` and does the following:

1. Triggers on pushes to the `main` branch that modify Python files or can be manually triggered
2. Generates .mdx documentation files from the Python examples
3. Clones the Prefect repository
4. Copies the generated docs to the Prefect repo's `docs/v3/examples` directory
5. Creates a pull request to the Prefect repository with the changes

## Manual Triggering

You can manually trigger the workflow by:

1. Going to the "Actions" tab in your repository
2. Selecting the "Generate and Deploy Example Docs" workflow
3. Clicking "Run workflow" → "Run workflow"

## Troubleshooting

If the workflow fails, check the following:

- Ensure your GH_PAT is valid and has the correct permissions
- Verify that the `internal/requirements.txt` file contains all dependencies needed to run the documentation generation
- Check that the paths in the workflow file match your repository structure 