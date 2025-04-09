from typing import Any, TypeVar

import marvin

from prefect import task, Task
from prefect.cache_policies import INPUTS, TASK_SOURCE
from prefect.states import State
from prefect.task_worker import serve
from prefect.client.schemas.objects import TaskRun

T = TypeVar("T")


def _print_output(task: Task, task_run: TaskRun, state: State[T]):
    result = state.result()
    print(f"result type: {type(result)}")
    print(f"result: {result!r}")


@task(cache_policy=INPUTS + TASK_SOURCE, on_completion=[_print_output])
async def create_structured_output(data: Any, target: type[T], instructions: str) -> T:
    return await marvin.cast_async(
        data,
        target=target,
        instructions=instructions,
    )


def main():
    serve(create_structured_output)


if __name__ == "__main__":
    main()
