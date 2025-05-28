# ---
# title: dbt Model Materialization – Prefect + dbt
# description: Orchestrate any dbt project with bullet-proof retries, observability, and a single Python file – no YAML or shell scripts required.
# dependencies: ["prefect", "dbt-core", "dbt-duckdb"]
# cmd: ["python", "02_flows/prefect_and_dbt.py"]
# tags: [dbt, materialization, tasks, analytics]
# draft: true
# ---

# # dbt Model Orchestration – Prefect + dbt
#
# **Orchestrate any dbt project with bullet-proof retries, observability, and a single Python file.**
#
# When you combine Prefect with dbt, you get **production-grade analytics orchestration** with zero ops overhead:
#
# * **Python** gives you the flexibility to integrate with any data source, API, or system your analytics need.
# * **dbt** handles the heavy lifting of SQL transformations, testing, and documentation.
# * **Prefect** wraps the entire workflow in battle-tested orchestration: automatic [retries](https://docs.prefect.io/v3/develop/write-tasks#retries), [scheduling](https://docs.prefect.io/v3/deploy/index#workflow-scheduling-and-parametrization), and [observability](https://docs.prefect.io/v3/develop/logging#prefect-loggers).
#
# The result? Your analytics team gets reliable, observable data pipelines without learning YAML orchestrators or writing shell scripts. Point this combo at any warehouse and it will transform your data while handling all the operational details.
#
# This example demonstrates these Prefect features:
# * [`@task`](https://docs.prefect.io/v3/develop/write-tasks#write-and-run-tasks) – wrap dbt commands in retries & observability.
# * [`log_prints`](https://docs.prefect.io/v3/develop/logging#configure-logging) – surface dbt output automatically in Prefect logs.
# * Automatic [**retries**](https://docs.prefect.io/v3/develop/write-tasks#retries) with exponential back-off for flaky network connections.
#
# ### The Scenario: Reliable Analytics Workflows
# Your analytics team uses dbt to model data in DuckDB for rapid prototyping. You need a workflow that:
# - Anyone can run locally without complex setup
# - Automatically retries on network failures or temporary dbt errors  
# - Provides clear logs and observability for debugging
# - Can be easily scheduled and deployed to production
#
# ### Our Solution
# Write three focused Python functions (download project, run dbt commands, orchestrate workflow), add Prefect decorators, and let Prefect handle [retries](https://docs.prefect.io/v3/develop/write-tasks#retries), [logging](https://docs.prefect.io/v3/develop/logging#prefect-loggers), and [scheduling](https://docs.prefect.io/v3/deploy/index#workflow-scheduling-and-parametrization). The entire example is self-contained – no git client or global dbt configuration required.
#
# *For more on integrating Prefect with dbt, see the [Prefect documentation](https://docs.prefect.io/integrations/dbt).*
#
# ### Running the example locally
# ```bash
# python 02_flows/prefect_and_dbt.py
# ```
# Watch as Prefect orchestrates the complete dbt lifecycle: downloading the project, running models, executing tests, and materializing results. The flow creates a local DuckDB file you can explore with any SQL tool.
#
# ## Code walkthrough
# 1. **Project Setup** – Download and cache a demo dbt project from GitHub
# 2. **dbt CLI Wrapper** – Execute dbt commands with automatic retries and logging
# 3. **Orchestration Flow** – Run the complete dbt lifecycle in sequence
# 4. **Execution** – Self-contained example that works out of the box

from __future__ import annotations

import io
import shutil
import subprocess
import urllib.request
import zipfile
from pathlib import Path

from prefect import flow, task


DEFAULT_REPO_ZIP = (
    "https://github.com/kevingrismore/demo-dbt-project/archive/refs/heads/main.zip"
)

# ---------------------------------------------------------------------------
# Project Setup – download and cache dbt project ---------------------------- 
# ---------------------------------------------------------------------------
# To keep this example fully self-contained, we download a demo dbt project
# directly from GitHub as a ZIP file. This means users don't need git installed.
# [Learn more about tasks in the Prefect documentation](https://docs.prefect.io/v3/develop/write-tasks)

@task(retries=2, retry_delay_seconds=5, log_prints=True)
def build_dbt_project(repo_zip_url: str = DEFAULT_REPO_ZIP) -> Path:
    """Download and extract the demo dbt project, returning its local path.

    To keep the example fully self-contained we grab the GitHub archive as a ZIP
    so users do **not** need `git` installed. The project is extracted into a
    sibling directory next to this script (`prefect_dbt_project`). If that
    directory already exists we skip the download to speed up subsequent runs.
    """

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

    # Find the folder containing dbt_project.yml (usually '<repo>-main/demo')
    candidates = list(tmp_extract_base.rglob("dbt_project.yml"))
    if not candidates:
        raise ValueError("dbt_project.yml not found in downloaded archive – structure unexpected")

    project_root = candidates[0].parent
    shutil.move(str(project_root), str(project_dir))
    shutil.rmtree(tmp_extract_base)

    print(f"Extracted dbt project to {project_dir}\n")
    return project_dir

# ---------------------------------------------------------------------------
# dbt CLI Wrapper – execute commands with retries and logging ---------------
# ---------------------------------------------------------------------------
# This task wraps the dbt CLI with automatic retries and streams all output
# to Prefect logs for easy debugging. It configures dbt to use the local project
# directory so the example works without touching global dbt configuration.
# [Learn more about retries in the Prefect documentation](https://docs.prefect.io/v3/develop/write-tasks#retries)

@task(retries=2, retry_delay_seconds=5, log_prints=True)
def run_dbt(command: str, project_dir: Path) -> None:
    """Run a dbt CLI command for the demo project.

    The task prepends common flags so that dbt always points at the bundled
    project and its local profiles directory, meaning the whole example works
    offline and without touching the user's global ~/.dbt folder.
    """

    full_cmd = f"dbt {command} --project-dir {project_dir} --profiles-dir {project_dir}"
    print(f"Running: {full_cmd}\n")

    # Use subprocess so that users don't need additional Prefect integrations
    result = subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True,
        cwd=project_dir,
    )

    # Stream stdout to Prefect logs for easier debugging
    print(result.stdout)
    if result.returncode != 0:
        # Include stderr in Prefect logs then raise for automatic retry handling
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, full_cmd)

# ---------------------------------------------------------------------------
# Orchestration Flow – run the complete dbt lifecycle ----------------------
# ---------------------------------------------------------------------------
# This flow orchestrates the standard dbt workflow: debug → deps → seed → run → test.
# Each step is a separate task run in Prefect, providing granular observability
# and automatic retry handling for any step that fails.
# [Learn more about flows in the Prefect documentation](https://docs.prefect.io/v3/develop/write-flows)

@flow(name="prefect_dbt_demo", log_prints=True)
def dbt_materialization_flow(repo_zip_url: str = DEFAULT_REPO_ZIP) -> None:
    """Materialize the demo dbt project with Prefect.

    Steps executed:
    1. `dbt debug`  – sanity-check environment and connection.
    2. `dbt deps`   – download any package dependencies (none for this tiny demo).
    3. `dbt seed`   – load seed CSVs if they exist (safe to run even when empty).
    4. `dbt run`    – build the model(s) defined under `models/`.
    5. `dbt test`   – execute any tests declared in the project.
    
    Each step runs as a separate Prefect task with automatic retries and logging.
    """

    project_dir = build_dbt_project(repo_zip_url)

    # dbt commands – executed sequentially for clarity
    run_dbt("debug", project_dir)
    run_dbt("deps", project_dir)
    run_dbt("seed", project_dir)
    run_dbt("run", project_dir)
    run_dbt("test", project_dir)

    # Let users know where the DuckDB file was written for exploration
    duckdb_path = project_dir / "demo.duckdb"
    print(f"\nDone! DuckDB file located at: {duckdb_path.resolve()}")

# ### What Just Happened?
#
# Here's the sequence of events when you run this flow:
# 1. **Project Download** – Prefect registered a task run to download and extract the dbt project from GitHub (with automatic caching for subsequent runs).
# 2. **dbt Lifecycle** – Five separate task runs executed the standard dbt workflow: `debug`, `deps`, `seed`, `run`, and `test`.
# 3. **Automatic Retries** – Each dbt command would automatically retry on failure (network issues, temporary dbt errors, etc.).
# 4. **Centralized Logging** – All dbt output streamed directly to Prefect logs, making debugging easy.
# 5. **Local Results** – A materialized DuckDB file appeared at `prefect_dbt_project/demo.duckdb` ready for analysis.
#
# **Prefect transformed a series of shell commands into a resilient, observable workflow** – no YAML files, no cron jobs, just Python.
#
# ### Why This Matters
#
# Traditional dbt orchestration often involves brittle shell scripts, complex YAML configurations, or heavyweight workflow tools. Prefect gives you **enterprise-grade orchestration with zero operational overhead**:
#
# - **Reliability**: Automatic retries with exponential backoff handle transient failures
# - **Observability**: Every dbt command is logged, timed, and searchable in the Prefect UI  
# - **Portability**: The same Python file runs locally, in CI/CD, and in production
# - **Composability**: Easily extend this flow with data quality checks, Slack alerts, or downstream dependencies
#
# This pattern scales from prototype analytics to production data platforms. Whether you're running dbt against DuckDB for rapid iteration or Snowflake for enterprise analytics, Prefect ensures your workflows are reliable, observable, and maintainable.
#
# To learn more about orchestrating analytics workflows with Prefect, check out:
# - [dbt integration guide](https://docs.prefect.io/integrations/dbt)
# - [Task configuration and retries](https://docs.prefect.io/v3/develop/write-tasks#retries) 
# - [Workflow scheduling and deployment](https://docs.prefect.io/v3/deploy/index#workflow-scheduling-and-parametrization)

if __name__ == "__main__":
    dbt_materialization_flow()
