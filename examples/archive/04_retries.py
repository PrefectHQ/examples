# ---
# title: Retries
# description: Showcase Prefect's built-in retry features at both the task and flow level, including custom conditions.
# dependencies: ["prefect", "httpx"]
# cmd: ["python", "04_misc/04_retries.py"]
# tags: [retries, tasks, flows]
# ---

# ## Prefect Retries – keep transient errors from sinking your workflow 📈
#
# Prefect offers first-class retry primitives:
# * `retries` – How many times to *re-execute* after failure. Setting `retries=2`
#   means the code runs up to **three** times total (initial attempt + 2 retries).
# * `retry_delay_seconds` – Wait period before the next attempt. Can be:
#   - A single value: `retry_delay_seconds=5` (5-second delay for all retries)
#   - A list: `retry_delay_seconds=[3, 9]` (3s for first retry, 9s for second)
# * `retry_condition_fn` – Optional predicate executed after a failure to
#   decide programmatically whether a retry should occur (perfect for
#   selective HTTP status handling).
#
# For a deeper dive into Prefect retries, see the official documentation:
# <https://docs.prefect.io/v3/develop/write-tasks#retries>
#
# ### When should you use retries?
# * **Network calls** – External APIs occasionally return 5xx errors or time out
# * **Cloud resources** – Services might throttle or rate-limit your requests
# * **Database access** – Table locks or connection limits may resolve with a pause
# * **File operations** – Occasional file locking or write contention
#
# ### Tasks vs. Flows
# * **Task retries** re-run only the failing unit of work; upstream task
#   results are cached and reused.
# * **Flow retries** re-execute the entire workflow graph.
#
# **Best practice**: Use task-level retries for isolated points of failure (like API
# calls), and add flow-level retries for systemic issues that might affect
# multiple tasks (like authentication or infrastructure outages).
#
# Below we demonstrate numeric retries *and* a custom `retry_on_503` predicate
# that retries only on HTTP 503 Service Unavailable responses.
#
# ---
# ### Running the example locally
# ```bash
# python 02_sdk_concepts/02_retries.py
# ```
# When you run this script, Prefect will schedule the GitHub tasks and attempt the
# `mimic_api_call` task up to three times (0 s, +3 s, +9 s).  The final
# log message confirms Prefect exhausted the retry budget before erroring gracefully.
#
# ---
# ## Code organization
# 1. **Imports & setup** – Just `prefect` and `httpx` for API calls
# 2. **Custom retry predicate** – Selective retry based on HTTP status code
# 3. **Task definitions** – GitHub repo data fetching with basic retries
# 4. **Flow definition** – Orchestration layer that runs all tasks in sequence
# 5. **Execution** – Entry point to run the example locally

from typing import Any

import httpx
from prefect import Task, flow, task
from prefect.client.schemas.objects import TaskRun
from prefect.states import State

# ---------------------------------------------------------------------------
# Custom retry predicate: return True to trigger a retry, False otherwise ----
# ---------------------------------------------------------------------------
# The helper predicate defined just below is used in tandem with the
# `mimic_api_call` task (declared later in this file).  That task reaches out to
# `https://httpbin.org/status/503` – an endpoint that intentionally responds with
# HTTP 503 Service Unavailable. This creates a reliable way to demonstrate
# Prefect's selective retry logic.
#
# The retry condition function:
# 1. Receives the task, task run, and current state
# 2. Inspects the underlying exception (if any)
# 3. Returns `True` only for 503 errors, `False` for everything else
#
# This way, transient "Service Unavailable" errors trigger retries, but all other
# errors (like 404 Not Found) fail immediately without wasting retry attempts.


def retry_on_503(task: Task[..., Any], task_run: TaskRun, state: State[Any]) -> bool:
    """Retry only when the task failed with an HTTP 503 error."""

    try:
        # Re-raise the original exception (if any) so we can inspect it
        state.result()
    except Exception as exc:
        if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 503:
            return True
    return False


@task(
    retries=2,  # total of 3 attempts (initial call + 2 retries)
    retry_delay_seconds=[3, 9],  # staggered back-off
    retry_condition_fn=retry_on_503,
)
def mimic_api_call() -> str:
    """Simulate a flaky API by calling an endpoint that always returns HTTP 503."""

    response = httpx.get("https://httpbin.org/status/503")
    response.raise_for_status()  # raises HTTPStatusError on 503
    return response.text


@task(retries=2, retry_delay_seconds=5)
def get_repo_info(repo_owner: str, repo_name: str):
    """Fetch repository metadata from GitHub API, with automatic retries."""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    api_response = httpx.get(url)
    api_response.raise_for_status()
    repo_info = api_response.json()
    return repo_info


@task(retries=2, retry_delay_seconds=5)
def get_contributors(repo_info: dict):
    """Fetch contributor list for a GitHub repository, with automatic retries."""
    contributors_url = repo_info["contributors_url"]
    response = httpx.get(contributors_url)
    response.raise_for_status()
    contributors = response.json()
    return contributors


@flow(log_prints=True)
def repo_info(repo_owner: str = "PrefectHQ", repo_name: str = "prefect"):
    """
    Fetch and display GitHub repository statistics.

    Retrieves star count and contributor count for the specified repository,
    with built-in resilience via task-level retries.
    """

    repo_info = get_repo_info(repo_owner, repo_name)
    print(f"Stars 🌠 : {repo_info['stargazers_count']}")

    contributors = get_contributors(repo_info)
    print(f"Number of contributors 👷: {len(contributors)}")

    upload = mimic_api_call()  # noqa


# ### What just happened?
# After the two GitHub API tasks succeeded (retrying if needed), Prefect ran
# `mimic_api_call`, which deliberately hit an endpoint returning 503 errors.
#
# Here's the sequence of events:
# 1. First attempt fails with HTTP 503
# 2. `retry_on_503` returns `True`, so Prefect waits 3 seconds
# 3. Second attempt also fails with HTTP 503
# 4. `retry_on_503` returns `True` again, so Prefect waits 9 seconds
# 5. Third attempt fails, but we've exhausted our retry budget (retries=2)
#
# Most importantly: the flow itself didn't crash, and all previously successful
# task results (GitHub stats) were preserved and displayed.
#
# **Resilience is critical for production data pipelines.** Without retries,
# even highly reliable systems (99.9% uptime) would fail daily at scale.
#
# Prefect's retry system:
# * **Eliminates boilerplate** – No more nested try/except blocks or complex retry loops
# * **Provides observability** – Tracks all attempts and surfaces them in the UI
# * **Enables fine-grained control** – Set different policies for different tasks
# * **Adapts intelligently** – Use condition functions to retry only when appropriate
#
# ### Why This Is Important
#
# Retries turn transient failures into minor blips and give your workflows production-grade resilience without cluttering your business logic with try/except loops. They ensure data pipelines remain reliable even when external systems are flaky.
#
# By moving retry logic from your business code to Prefect's declarative layer,
# you get a more maintainable, observable, and resilient workflow with less code.

if __name__ == "__main__":
    repo_info()
