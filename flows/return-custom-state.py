"""
Demonstrates directly returning a state. In this case, an AwaitingRetry state
which causes a task to be retried after a delay.
"""

from datetime import datetime, timedelta, UTC

from prefect import task, get_run_logger
from prefect.context import get_run_context
from prefect.states import AwaitingRetry


@task
def main():
    get_run_logger().info("Running main task")

    # In practice we might fetch a URL that is temporarily unavailable
    # and retry after a number of seconds specified by a Retry-After header
    retry_after = 10

    # Break out of the retry loop after the first run
    ctx = get_run_context()
    if ctx.task_run.run_count > 1:
        return

    # Schedule the task to run again in {retry_after} seconds
    return AwaitingRetry(
        scheduled_time=datetime.now(UTC) + timedelta(seconds=retry_after)
    )


if __name__ == "__main__":
    main()
