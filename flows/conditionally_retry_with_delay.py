# /// script
# dependencies = ["prefect", "httpx"]
# ///

"""
Demonstrates using built-in retry functionality to retry a task after a delay
when specific HTTP status codes are encountered.
"""

from typing import Any

import httpx
from prefect import Task, task
from prefect.client.schemas.objects import TaskRun
from prefect.states import State


def retry_on_503(task: Task[..., Any], task_run: TaskRun, state: State[Any]) -> bool:
    try:
        state.result()
    except Exception as e:
        if isinstance(e, httpx.HTTPStatusError) and e.response.status_code == 503:
            return True
    return False


@task(
    retries=2,
    retry_delay_seconds=[3, 9],
    retry_condition_fn=retry_on_503,
)
def make_api_call():
    response = httpx.get("https://httpbin.org/status/503")
    response.raise_for_status()
    return response.text


if __name__ == "__main__":
    make_api_call()
