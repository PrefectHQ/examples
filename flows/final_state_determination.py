# /// script
# dependencies = ["prefect>=3.0.0"]
# ///

"""
This example demonstrates flow final state determination based on task states.
"""

import time

from prefect import flow, task
from prefect.futures import PrefectFuture, wait
from prefect.states import State, StateType


@task
def waiting_task(seconds: int) -> int:
    time.sleep(seconds)
    return seconds


@task
def failing_task(seconds: int):
    time.sleep(seconds)
    raise ValueError("Task failed (as expected)")


@flow
def example_flow(return_completed_states: bool = False) -> list[State[int | None]]:
    # Submit three tasks that depend on each other sequentially (a -> b -> c)
    a: PrefectFuture = waiting_task.submit(1)
    b: PrefectFuture = failing_task.submit(1, wait_for=[a])
    c: PrefectFuture = waiting_task.submit(1, wait_for=[b])

    # Wait for all futures to complete using the wait utility
    wait([a, b, c])

    if return_completed_states:  # bail out with completed states -> Completed flow run
        return [
            future.state
            for future in [a, b, c]
            if future.state.type == StateType.COMPLETED
        ]

    # Return all states -> Failed flow run since b failed
    return [a.state, b.state, c.state]


if __name__ == "__main__":
    resulting_states = example_flow()
    assert [state.type for state in resulting_states] == [
        StateType.COMPLETED,
        StateType.FAILED,
        StateType.PENDING,  # c could not run, as b failed
    ]

    completed_states = example_flow(return_completed_states=True)
    assert [state.type for state in completed_states] == [StateType.COMPLETED]
    assert completed_states[0].result() == 1
