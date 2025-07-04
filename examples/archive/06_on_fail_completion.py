# ---
# title: Flow callbacks
# description: Learn how to respond dynamically to completion or failure of your workflows with Prefect's built-in callback system.
# dependencies: ["prefect", "httpx"]
# cmd: ["python", "04_misc/06_on_fail_completion.py"]
# tags: [callbacks, logging]
# ---

# ## Responding intelligently to flow outcomes
#
# Great data workflows don't just execute steps—they respond intelligently to
# both success and failure conditions. Whether you're running critical ETL jobs,
# ML model training, or scheduled reports, you need visibility when things go right
# and rapid response when they don't.
#
# Prefect's callback system provides a clean, declarative way to handle both outcomes:
#
# ```python
# @flow(
#     on_completion=notify_team_success,  # Called when flow completes successfully
#     on_failure=alert_ops_team,       # Called when flow fails
# )
# def my_important_workflow():
#     ...
# ```
#
# ### What are callbacks?
#
# Callbacks are Python functions that execute at specific flow lifecycle points:
#
# * **on_completion** – runs after successful completion (COMPLETED state)
# * **on_failure** – runs after failure (FAILED state)
#
# Each callback receives two arguments:
# 1. The flow object itself
# 2. The final Prefect State object (with runtime, result, and details)
#
# Because callbacks execute in the same process as your flow, they have access to
# your entire Python environment—perfect for sending webhooks, logging to external
# systems, or triggering downstream processes.
#
# For more details, see Prefect's callback documentation:
# <https://docs.prefect.io/v3/develop/manage-states>
#
# ### When should you use callbacks?
# * **Monitoring & Alerting** – Get Slack/Teams alerts when critical pipelines fail
# * **Cleanup tasks** – Ensure resources (temp files, clusters) are cleaned regardless of outcome
# * **Workflow chaining** – Trigger downstream flows only when upstream succeeds
# * **Metadata reporting** – Push run metrics to observability tools on success
#
# In this example, we'll implement two callbacks that attach to a GitHub repository
# stats flow. One handles successful completion by displaying runtime metrics, while
# the other creates a diagnostic message when the flow fails.

import httpx
from prefect import flow, task

# ---------------------------------------------------------------------------
# Callback helpers -----------------------------------------------------------
# ---------------------------------------------------------------------------


def log_failure(flow_obj, state):
    """Callback executed when the flow ends in a FAILED state."""

    print(
        "\n🚨 Flow FAILED – "
        f"name={flow_obj.name!r} • run_id={state.state_details.flow_run_id}"
    )


def log_success(flow_obj, state):
    """Callback executed when the flow ends in a COMPLETED state."""

    duration = state.state_details.duration  # seconds
    print("\n✅ Flow SUCCEEDED – " f"name={flow_obj.name!r} • duration={duration:.2f}s")


@task(retries=2, retry_delay_seconds=5)
def get_repo_info(repo_owner: str, repo_name: str):
    """Get info about a repo - will retry twice after failing"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    api_response = httpx.get(url)
    api_response.raise_for_status()
    repo_info = api_response.json()
    return repo_info


@task(retries=2, retry_delay_seconds=5)
def get_contributors(repo_info: dict):
    """Get contributors for a repo"""
    contributors_url = repo_info["contributors_url"]
    response = httpx.get(contributors_url)
    response.raise_for_status()
    contributors = response.json()
    return contributors


@flow(
    name="github-repo-stats-with-callbacks",
    log_prints=True,
    retries=2,
    retry_delay_seconds=5,
    on_failure=[log_failure],
    on_completion=[log_success],
)
def repo_info(repo_owner: str = "PrefectHQ", repo_name: str = "prefect"):
    """
    Given a GitHub repository, logs the number of stargazers
    and contributors for that repo.
    """
    repo_info = get_repo_info(repo_owner, repo_name)
    print(f"Stars 🌠 : {repo_info['stargazers_count']}")

    contributors = get_contributors(repo_info)
    print(f"Number of contributors 👷: {len(contributors)}")


# ### Why This Is Important
# Callbacks give you a single, declarative place to hook monitoring, alerting,
# or cleanup logic—separating *business* code from *operational* concerns.  No
# more scattering `try/except` blocks or forgotten Slack calls throughout your
# pipeline; Prefect guarantees the callback runs exactly once per flow run.

if __name__ == "__main__":
    repo_info()
