# ---
# title: Automatic Asset Tracking for dbt Models - Zero Configuration Required
# description: Get asset-like observability for every dbt model with PrefectDbtRunner – no decorators, no boilerplate, just run dbt.
# dependencies: ["prefect", "prefect-dbt>=0.7.2", "dbt-core", "dbt-duckdb"]
# cmd: ["python", "02_flows/dbt_models_as_assets.py"]
# tags: [assets, events, dbt, lineage, observability, automation]
# draft: false
# ---
#
# # Automatic Asset Tracking for dbt Models
#
# When you run dbt models with PrefectDbtRunner, they automatically appear as [assets](https://docs.prefect.io/v3/concepts/assets) in
# Prefect Cloud with full lineage and execution history. No decorators or configuration needed.
#
# ## What You Get
#
# - Every dbt model becomes a trackable asset with visual lineage
# - Execution history and status for each model
# - Automatic dependency tracking
# - Event-based automations for failures and performance monitoring
#
# This feature requires Prefect Cloud and prefect-dbt version 0.7.2+.
#
# ## The Code

import io
import shutil
import urllib.request
import zipfile
from pathlib import Path

from prefect import flow, task
from prefect_dbt import PrefectDbtRunner, PrefectDbtSettings

# This is a zip archive of the Prefect examples repo, used here to fetch a sample dbt project for demonstration.
DEFAULT_REPO_ZIP = "https://github.com/PrefectHQ/examples/archive/refs/heads/main.zip"

# ---------------------------------------------------------------------------
# Setup Tasks


@task(retries=2, retry_delay_seconds=5, log_prints=True)
def build_dbt_project(repo_zip_url: str = DEFAULT_REPO_ZIP) -> Path:
    """Download and extract the demo dbt project, returning its local path."""

    project_dir = Path(__file__).parent / "prefect_dbt_project"
    if project_dir.exists():
        print(f"Using cached dbt project at {project_dir}\n")
        return project_dir

    tmp_extract_base = project_dir.parent / "_tmp_dbt_extract"
    if tmp_extract_base.exists():
        shutil.rmtree(tmp_extract_base)

    print(f"Downloading dbt project archive → {repo_zip_url}\n")
    with urllib.request.urlopen(repo_zip_url) as resp:
        data = resp.read()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(tmp_extract_base)

    candidates = list(
        tmp_extract_base.rglob("**/resources/prefect_dbt_project/dbt_project.yml")
    )
    if not candidates:
        raise ValueError("dbt_project.yml not found in resources/prefect_dbt_project")

    project_root = candidates[0].parent
    shutil.move(str(project_root), str(project_dir))
    shutil.rmtree(tmp_extract_base)

    print(f"Extracted dbt project to {project_dir}\n")
    return project_dir


@task(retries=2, retry_delay_seconds=5, log_prints=True)
def create_dbt_profiles(project_dir: Path) -> None:
    """Create a profiles.yml file for DuckDB connection."""

    profiles_content = f"""demo:
  outputs:
    dev:
      type: duckdb
      path: {project_dir}/demo.duckdb
      threads: 1
  target: dev"""

    profiles_path = project_dir / "profiles.yml"
    with open(profiles_path, "w") as f:
        f.write(profiles_content)

    print(f"Created/updated profiles.yml at {profiles_path}")


# ---------------------------------------------------------------------------
# Automatic Asset Tracking with PrefectDbtRunner


@task(retries=2, retry_delay_seconds=5, log_prints=True)
def run_dbt_with_automatic_tracking(project_dir: Path, commands: list[str]) -> None:
    """Run dbt commands with automatic asset tracking through Prefect events."""

    settings = PrefectDbtSettings(
        project_dir=str(project_dir), profiles_dir=str(project_dir)
    )

    # Use raise_on_failure=False to ensure events are created even when tests fail
    runner = PrefectDbtRunner(settings=settings, raise_on_failure=False)

    for command in commands:
        print(f"Running: dbt {command}")
        result = runner.invoke(command.split())
        print(f"Completed: dbt {command} (success: {result.success})")


# ---------------------------------------------------------------------------
# Main Flow


@flow(name="dbt_automatic_assets_flow", log_prints=True)
def dbt_automatic_assets_flow(repo_zip_url: str = DEFAULT_REPO_ZIP) -> None:
    """Run dbt models with automatic asset tracking in Prefect Cloud.

    Every dbt model execution creates events that populate the Assets view
    with visual lineage and execution history - no configuration needed.
    """

    # Setup the dbt project
    project_dir = build_dbt_project(repo_zip_url)
    create_dbt_profiles(project_dir)

    # Run dbt commands - automatic events are created for every model!
    run_dbt_with_automatic_tracking(project_dir, ["deps", "build"])

    duckdb_path = project_dir / "demo.duckdb"
    print(f"\n🎉 dbt pipeline complete! DuckDB file: {duckdb_path.resolve()}")
    print("\n📊 Check Prefect Cloud to see automatic asset tracking!")
    print("\n🗂️ In the Assets view:")
    print("   • See your dbt models with visual lineage")
    print("   • Track when each asset was last materialized")
    print("   • Search assets by name or URI")
    print("\n🔔 In the Events page:")
    print("   • View detailed execution history")
    print("   • Create automations based on asset events")
    print("   • Monitor test failures and performance")
    print("\n✨ No @materialize decorator needed - automatic tracking!")


# ## See It In Action
#
# After running this flow, navigate to Prefect Cloud:
#
# **Assets View**: Your dbt models appear with visual lineage showing dependencies
# **Events Page**: Full [execution history](https://docs.prefect.io/v3/concepts/events#events) including tests and timing data
#
# ## Why This Matters
#
# This isn't just about prettier dashboards. It's about fundamentally changing how you work
# with dbt at scale. When a critical model fails at 3 AM, your on-call engineer doesn't need
# to piece together what happened from scattered logs. They open the Assets view, see exactly
# which model failed, trace its downstream impacts, and fix the issue in minutes instead of hours.
#
# For new team members, onboarding becomes trivial. Instead of learning a custom asset
# framework, they simply run their dbt models with [PrefectDbtRunner](https://docs.prefect.io/integrations/prefect-dbt) and immediately get the
# same visibility as everyone else. No decorators to learn, no definitions to maintain.
#
# The broader principle here is that infrastructure should enhance your work, not define it.
# By inferring assets from actual execution rather than requiring upfront declarations,
# Prefect keeps the focus where it belongs: on the transformations that drive your business.
# This automatic tracking works alongside Prefect's `@materialize` decorator, giving you the
# flexibility to use explicit assets when you need fine-grained control and automatic tracking
# for everything else.
#
# Start with what works, evolve as you need.

if __name__ == "__main__":
    dbt_automatic_assets_flow()
    # Deploy for scheduled runs:
    # dbt_automatic_assets_flow.serve(
    #     name="dbt-asset-tracking",
    #     cron="0 6 * * *"  # Daily at 6 AM
    # )

# To learn more about this, [check out our blog post](https://www.prefect.io/blog/turn-your-dbt-project-into-a-production-pipeline-in-minutes).
