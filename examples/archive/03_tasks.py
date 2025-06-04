# ---
# title: Tasks with retries (GitHub API)
# description: Learn about Prefect's **Task** abstraction – the core building block for modular, reusable workflow components.
# dependencies: ["prefect", "httpx"]
# cmd: ["python", "04_misc/03_tasks.py"]
# tags: [tasks, retries, http]
# ---

# ## Tasks: The Core Concept of Prefect Workflows
#
# At its heart, Prefect's design revolves around **tasks**—the fundamental building
# blocks that define discrete units of work in your data pipelines. Think of tasks
# as specialized Python functions that gain superpowers through the `@task` decorator.
#
# ### What makes a task special?
#
# ```python
# @task
# def process_data(input_data):
#     # Your work here
#     return result
# ```
#
# By decorating a function with `@task`, you gain:
#
# * **Input/output tracking** – Prefect automatically logs parameters and return values
# * **State management** – Each task executes with a lifecycle (pending → running → completed)
# * **Concurrency control** – Run multiple tasks in parallel with configurable limits
# * **Result persistence** – Store outputs and reuse them across flow runs
# * **Caching** – Skip duplicate work when inputs haven't changed
# * **Retries** – Automatically recover from transient failures
# * **Observability** – Monitor, inspect, and debug task execution in the UI
#
# For a deeper dive into Prefect tasks, see the official documentation:
# <https://docs.prefect.io/latest/concepts/tasks/>
#
# ### When should you use tasks?
# * **Network / API calls** – Add retries, timeouts, and logging around external requests
# * **Data transformations** – Encapsulate heavyweight Pandas / Spark operations for caching
# * **Resource-intensive steps** – Delegate CPU / memory-heavy work to distributed workers
# * **Reusable logic** – Package common business logic so it can be shared across flows
#
# ### Tasks are composable
#
# Tasks work together through simple input/output connections. A task returns a regular
# Python object, which can be passed to other tasks or used directly within a flow.
# This creates a clean dependency graph that Prefect uses for execution.
#
# ### In this example
#
# We'll build a simple workflow with two tasks that fetch GitHub data:
# 1. `get_repo_info` – Retrieves basic information about a repository
# 2. `get_contributors` – Fetches the list of contributors using the URL from the first task
#
# The second task includes retry logic for resilience against API rate limiting or
# network issues. We'll orchestrate everything with a flow that logs the repository's
# star count and contributor count.
#
# ### Running the example
# ```bash
# python 02_sdk_concepts/01_tasks.py
# ```


import httpx
from prefect import flow, task

# ---------------------------------------------------------------------------
# Task definitions -----------------------------------------------------------
# ---------------------------------------------------------------------------

# ## Task definitions
#
# First, we'll define two tasks that interact with the GitHub API.
# Notice how each task:
# 1. Has a focused purpose (single responsibility)
# 2. Takes explicit inputs and returns processed outputs
# 3. Includes helpful docstrings


@task(name="fetch-repo-info")
def get_repo_info(repo_owner: str, repo_name: str) -> dict:
    """Fetch complete repository metadata from the GitHub API.

    Args:
        repo_owner: GitHub username or organization name
        repo_name: Name of the repository

    Returns:
        Dict containing repository metadata (stars, description, URLs, etc.)
    """

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


@task(
    name="fetch-contributors",
    retries=2,  # Try up to 3 times total (initial + 2 retries)
    retry_delay_seconds=5,  # Wait 5 seconds between attempts
)
def get_contributors(repo_info: dict) -> list[dict]:
    """Retrieve contributor information for a repository.

    This task demonstrates automatic retries - helpful when dealing with
    rate limiting or transient API errors.

    Args:
        repo_info: Repository metadata dict (from get_repo_info)

    Returns:
        List of contributor dictionaries with usernames and contribution counts
    """

    contributors_url = repo_info["contributors_url"]
    response = httpx.get(contributors_url)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Flow definition ------------------------------------------------------------
# ---------------------------------------------------------------------------

# ## Flow definition
#
# Now we'll create a flow that orchestrates our tasks. The flow:
# 1. Takes optional repo owner/name parameters
# 2. Calls the first task to get repository information
# 3. Extracts and displays the star count
# 4. Calls the second task to get contributor information
# 5. Displays the total number of contributors


@flow(
    log_prints=True,
    retries=2,
    retry_delay_seconds=5,
)
def repo_info(repo_owner: str = "PrefectHQ", repo_name: str = "prefect") -> None:
    """Log star & contributor counts for a GitHub repository."""

    repo = get_repo_info(repo_owner, repo_name)
    print(f"Stars 🌠 : {repo['stargazers_count']}")

    contributors = get_contributors(repo)
    print(f"Contributors 👷 : {len(contributors)}")


# ### What just happened?
#
# When you run this script, Prefect:
#
# 1. Registered the two task functions with the Prefect engine
# 2. Created a flow to coordinate their execution
# 3. Called the first task `get_repo_info` to retrieve repository data
# 4. Logged the star count from that data
# 5. Passed the repository data to the `get_contributors` task
# 6. Counted and displayed the number of contributors
#
# If any API calls had failed, Prefect would have automatically retried the
# `get_contributors` task according to its retry policy (twice with 5-second delays).
#
# ### Why This Is Important
#
# Tasks are the foundation of scalable, maintainable data workflows:
#
# * **Isolation**: Each task is an independently testable unit
# * **Resilience**: Tasks can retry on failure without rerunning the entire flow
# * **Visibility**: Tasks appear as separate nodes in the Prefect UI
# * **Performance**: Tasks can run concurrently or be distributed across workers
# * **Reusability**: Tasks can be imported and shared across multiple flows
#
# By breaking complex processes into discrete tasks, you gain both operational
# benefits (resilience, scalability) and development advantages (readability,
# maintainability, testing).

# ## Local execution

if __name__ == "__main__":
    repo_info()
