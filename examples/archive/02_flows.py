# ---
# title: Getting Started with Prefect Flows – Your First Real-World Workflow 🚀
# description: Learn how to build, parameterize, and run Prefect **flows** through a hands-on tutorial.
# deploy: false
# cmd: ["python", "04_misc/02_flows.py"]
# tags: [getting_started, flows, prefect]
# dependencies: ["prefect"]
# ---

# # Prefect Flows – A Hands-On Introduction
#
# This tutorial demonstrates some core features of Prefect:
#
# * Define reusable tasks with `@task`.
# * Combine those tasks into a `@flow`.
# * Add automatic retries and logging—no extra boilerplate required.
# * Run the flow locally and see logs in real time.
#
# ## Importing Prefect and setting up
#
# We start by importing the `task`, `flow`, and logging helpers from Prefect.

from datetime import datetime
from random import randint
from time import sleep

from prefect import flow, get_run_logger, task

# ---------------------------------------------------------------------------
# Component 1 – Define reusable tasks
# ---------------------------------------------------------------------------
# Tasks are the building blocks of a flow.  Each task executes a single piece of
# logic and can be retried, cached, or run in parallel.


@task(retries=2, retry_delay_seconds=5)
def fetch_data(size: int) -> list[int]:
    """Simulate pulling records from an API or database."""
    logger = get_run_logger()
    logger.info("Fetching %s rows of data…", size)
    # Simulate flaky network by randomly failing
    if randint(0, 4) == 0:
        raise RuntimeError("Random fetch failure – triggering retry…")
    sleep(1)
    return list(range(size))


@task
def transform(data: list[int]) -> list[int]:
    """A trivial transformation – square each number."""
    logger = get_run_logger()
    logger.info("Transforming %s rows…", len(data))
    return [x**2 for x in data]


@task
def load(data: list[int]) -> None:
    """Pretend to write the data somewhere (here we just log)."""
    logger = get_run_logger()
    logger.info("Loaded %s rows!", len(data))


# ---------------------------------------------------------------------------
# Component 2 – Compose a flow
# ---------------------------------------------------------------------------
# Flows orchestrate tasks. They can accept parameters, call tasks (or other
# flows), and return results.


@flow(log_prints=True)
def tutorial_flow(
    rows: int = 10,
    run_name: str = f"tutorial-run-{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}",
):
    """End-to-end example that fetches, transforms, and loads data.

    Args:
        rows: Number of rows to fetch.
        run_name: A friendly name that will appear in the Prefect UI.
    """
    logger = get_run_logger()
    logger.info("🗂️  Starting flow '%s' to process %s rows", run_name, rows)

    raw = fetch_data(rows)
    cleaned = transform(raw)
    load(cleaned)

    logger.info("✅ Flow completed!")
    return len(cleaned)


# ---------------------------------------------------------------------------
# What happens when you run this file?
# ---------------------------------------------------------------------------
# 1. Prefect registers the tasks (`fetch_data`, `transform`, `load`).
# 2. `tutorial_flow` is invoked within the `__main__` guard.
# 3. Logs appear in your terminal; retries happen automatically on failure.
# 4. Open the Prefect UI (prefect Orion) to see your run: `prefect orion start`.
#
# **Next steps**:
# * Experiment with different `rows` values.
# * Change `retries` or `retry_delay_seconds` on the `fetch_data` task.
# * Add a parameter to change the square exponent!

# ### Running the example locally
# ```bash
# python 01_getting_started/02_flows.py
# ```
# The script will fetch, transform, and "load" a configurable number of rows while printing logs to your terminal. Any transient failures in `fetch_data` trigger automatic retries.

# ## Code organization
# 1. **Imports & setup** – standard libraries plus `prefect` helpers
# 2. **Component 1 – reusable tasks** (`fetch_data`, `transform`, `load`)
# 3. **Component 2 – flow orchestration** (`tutorial_flow`)
# 4. **Execution guard** – runs the flow when the file is executed directly

# ### What just happened?
# When you executed the script, Prefect performed the following steps:
# 1. Registered the three tasks along with their retry logic.
# 2. Started a **flow run** named after the current timestamp.
# 3. Ran `fetch_data`; if it failed, Prefect retried up to 2 times.
# 4. Piped the successful output into `transform`, then into `load`.
# 5. Logged every step so you have full observability in the UI and CLI.
#
# **Key takeaway**: A flow bundles multiple tasks into a robust, observable unit of work that you can schedule, parameterize, and monitor—all with minimal boilerplate.

if __name__ == "__main__":
    # Run the flow with a custom parameter value
    tutorial_flow(rows=25)
