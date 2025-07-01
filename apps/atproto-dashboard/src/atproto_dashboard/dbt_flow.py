import configparser
import os
import subprocess
from datetime import datetime
from pathlib import Path

from prefect import flow, task
from prefect.artifacts import create_markdown_artifact
from prefect.assets import materialize

from atproto_dashboard.settings import settings


@task
def run_dbt_command(command: str, project_dir: Path) -> str:
    """Run a dbt command and return the output."""
    # Read AWS credentials from ~/.aws/credentials since they're not in env vars
    aws_creds_path = Path.home() / ".aws" / "credentials"
    aws_access_key_id = ""
    aws_secret_access_key = ""

    if aws_creds_path.exists():
        config = configparser.ConfigParser()
        config.read(aws_creds_path)
        if "default" in config:
            aws_access_key_id = config["default"].get("aws_access_key_id", "")
            aws_secret_access_key = config["default"].get("aws_secret_access_key", "")

    result = subprocess.run(
        f"dbt {command}",
        shell=True,
        cwd=project_dir,
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "DBT_PROFILES_DIR": str(project_dir),
            "AWS_BUCKET_NAME": settings.aws_bucket_name,
            # Pass AWS credentials explicitly for DuckDB
            "AWS_ACCESS_KEY_ID": aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": aws_secret_access_key,
        },
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt {command} failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )

    return result.stdout


@materialize(
    "duckdb://local/dbt-models",
    asset_deps=[
        f"s3://{settings.aws_bucket_name}/assets/starter-pack-members/latest.json",
        f"s3://{settings.aws_bucket_name}/assets/actor-feeds/latest.json",
    ],
)
def materialize_dbt_models() -> dict:
    """
    Build dbt models as a Prefect Asset.
    Returns metadata about the models built.
    """
    project_dir = Path(__file__).parent.parent.parent / "dbt_project"

    # Run dbt deps to install dependencies
    run_dbt_command("deps", project_dir)

    # Run dbt to build all models
    output = run_dbt_command("run", project_dir)

    # Parse output to extract model information
    lines = output.split("\n")
    models_built = []

    for line in lines:
        if "OK created" in line:
            # Extract model name from lines like "OK created table model dbt_project.stg_feeds"
            parts = line.split()
            if len(parts) > 4:
                model_name = parts[-1].split(".")[-1]
                models_built.append(model_name)

    stats_line = next((line for line in lines if "Completed" in line), "")

    result = {
        "models_built": models_built,
        "stats": stats_line,
        "timestamp": datetime.now().isoformat(),
    }

    create_markdown_artifact(
        key="dbt-models-built",
        markdown=f"""
# dbt Models Built

## Summary
{stats_line}

## Models
{chr(10).join(f"- {model}" for model in models_built)}

## Full Output
```
{output}
```
""",
        description="dbt model build results",
    )

    return result


@flow(name="transform-data")
def transform_data() -> dict:
    """
    Run dbt models to transform the ingested data.
    This flow depends on the ingestion assets.
    """
    # Materialize dbt models (creates the asset)
    result = materialize_dbt_models()

    summary = {
        "models_count": len(result["models_built"]),
        "models": result["models_built"],
        "stats": result["stats"],
    }

    return summary


if __name__ == "__main__":
    transform_data()
