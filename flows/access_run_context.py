# /// script
# dependencies = ["prefect"]
# ///

"""
Examples of accessing Prefect's runtime context to get information about the current flow run:
- List the fields in the context
- Access a few specific fields
- Get the URL for the flow run
"""

import prefect.runtime.flow_run
import prefect.runtime.task_run
from prefect import flow, task


@flow(log_prints=True)
def example_flow():
    # let's see what's available in the flow run runtime context
    for field in prefect.runtime.flow_run.__all__:
        print(f"{field}: {getattr(prefect.runtime.flow_run, field)}")

    # The runtime module supports dot notation for accessing attributes
    # for example, let's grab the flow run id
    print(f"\nThis flow run has id '{prefect.runtime.flow_run.id}'")

    # We can also get the dashboard URL for the flow run
    print(f"\n See this flow run in the UI: '{prefect.runtime.flow_run.ui_url}'")


@task(log_prints=True)
def example_task():
    # let's see what's available in the task run runtime context
    for field in prefect.runtime.task_run.__all__:
        print(f"{field}: {getattr(prefect.runtime.task_run, field)}")


if __name__ == "__main__":
    # Run the example flow from above
    example_flow()

    # Run the example task from above
    example_task()

    # Outside of a run context, `prefect.runtime` will return empty values
    assert prefect.runtime.flow_run.id is None
    assert prefect.runtime.task_run.id is None
