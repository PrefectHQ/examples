# ---
# title: Prefect SDK – A Gentle Introduction
# description: Turn ordinary Python scripts into resilient, observable workflows using Prefect's batteries-included SDK.
# dependencies: ["prefect"]
# cmd: ["python", "02_sdk_concepts/01_introduction.py"]
# tags: [sdk, overview]
# ---

# ## Why the Prefect SDK?
# Everyone writes Python scripts. Prefect keeps them alive in production.
# A single decorator wraps your functions with:
# • Automatic retries for transient failures
# • Instant logging (no logger setup required)
# • On-success and on-failure callbacks for smart alerts
# • Async & task concurrency with built-in runners
# • Transaction-like state management and checkpointing
# • A rich API & UI for monitoring and scheduling
#
# In short, if you can code it in python, you can wrap it with Prefect.

# ## Getting started in seconds
#
# 1️⃣ Install Prefect with the lightning-fast **uv** package manager:
#
# ```
# uv pip install prefect
# ```
#
# 2️⃣ Decorate your functions and run:

from prefect import flow, task


@task
def say_hello(name: str = "world"):
    print(f"Hello, {name}!")


@flow
def my_first_flow():
    say_hello("Prefect")


if __name__ == "__main__":
    my_first_flow()

# That's all it takes! No YAML, no config files, just pure Python fueled by Prefect.

# ## Why This Is Important
# Prefect transforms fragile scripts into production-grade workflows **without** the usual avalanche of
# boilerplate. Instead of sprinkling `try/except`, custom logging, and hand-rolled retry loops
# throughout your codebase, you declare that intent once, then Prefect handles the rest.
#
# **What you gain:**
# * **Observability out of the box** – Every run is tracked with rich metadata and searchable logs.
# * **Resilience by default** – A single `retries=` argument protects against transient failures.
# * **Separation of concerns** – Keep business logic readable while Prefect manages orchestration.
# * **Portability** – Run the same flow locally, on-prem, or in Prefect Cloud with zero code changes.
# * **Scalability** – Concurrency controls and async support let you fan-out work safely at any scale.
#
# The result? Faster iteration, fewer on-call headaches, and data pipelines you can trust in prime time.
