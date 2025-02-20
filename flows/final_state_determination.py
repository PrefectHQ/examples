# /// script
# dependencies = ["prefect>=3.0.0"]
# ///

"""
This example demonstrates flow final state determination based on task states.
"""

import time

from prefect import flow, task

# Imports for type annotations
from prefect.futures import PrefectFuture, PrefectFutureList


def wait_for_futures():
    """
    Wait for all assigned PrefectFuture and PrefectFutureList objects in the calling function's local scope. If you do not assign the return value of a task to a variable, it will not be waited for.
    """
    import inspect

    caller_locals = inspect.currentframe().f_back.f_locals

    for item in caller_locals.values():
        if isinstance(item, (PrefectFuture, PrefectFutureList)):
            item.wait()


@task
def wait(seconds: int) -> int:
    time.sleep(seconds)
    return seconds


@task
def fail(seconds: int):
    time.sleep(seconds)
    raise ValueError("Task failed successfully")


@flow
def subflow(behavior: str):
    # Submit three tasks that depend on each other sequentially (a -> b -> c)
    a: PrefectFuture = wait.submit(1)
    b: PrefectFuture = fail.submit(1, wait_for=[a])
    c: PrefectFuture = wait.submit(1, wait_for=[b])

    # The easiest option is to return the futures themselves
    # This will automatically wait for them to complete and fail the flow if any task fails
    if behavior == "futures":
        return [a, b, c]

    # Another option with more control is to wait for, and then return, the task states
    # In this case, the exception is not re-raised in the flow, but the flow will still fail
    elif behavior == "states":
        # First we wait for the tasks to complete
        # We'll use the wait_for_futures() helper but you could also do this manually:
        # [_task.wait() for _task in [a, b, c]]
        wait_for_futures()
        # Then we return the states
        return [a.state, b.state, c.state]

    # Another option is to re-raise any exceptions from the task in the flow
    # Calling .result() will wait for the task to complete
    elif behavior == "raise":
        [item.result(raise_on_failure=True) for item in [a, b, c]]

    else:
        raise ValueError(f"Invalid behavior: {behavior}")


@flow
def main():
    subflow("futures")
    subflow("states")
    subflow("raise")


if __name__ == "__main__":
    main()
