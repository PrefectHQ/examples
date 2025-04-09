import inspect
from typing import Any, Callable

import marvin

from prefect import task
from prefect.cache_policies import INPUTS, TASK_SOURCE
from prefect.task_worker import serve


def _print_output(output: Any):
    print(f"result type: {type(output)}")
    print(f"result: {output!r}")


@task(cache_policy=INPUTS + TASK_SOURCE)
async def cast_data_to_type[T](
    data: Any,
    target: type[T],
    instructions: str,
    on_complete: Callable[[T], None] | None = _print_output,
) -> T:
    output = await marvin.cast_async(
        data,
        target=target,
        instructions=instructions,
    )

    if on_complete:
        if inspect.iscoroutinefunction(on_complete):
            await on_complete(output)
        else:
            on_complete(output)

    return output


def main():
    """main entrypoint for the task"""
    serve(cast_data_to_type)


if __name__ == "__main__":
    main()
