"""
Examples of using Prefect's context to get information about the current flow run:
- List the fields in the context
- Access a few specific fields
- Get the URL for the flow run
"""

from prefect import flow, task, get_run_logger
from prefect.context import get_run_context
from prefect.utilities.urls import url_for


@flow
def example_flow():
    ctx = get_run_context()
    logger = get_run_logger()

    # Calling get_run_context in a flow run returns an EngineContext object
    # EngineContext was previously called (and is aliased as) FlowRunContext
    logger.info(f"\nContext has type '{type(ctx)}'")

    # List out the keys in the context
    logger.info("\nContext has the following fields:")
    for field in sorted(ctx.model_fields.keys()):
        logger.info(field)

    # Context is an object, not just a dictionary
    # For example, let's grab the flow run id
    logger.info(f"\nThis flow run has id '{ctx.flow_run.id}'")

    # We can also get the URL for the flow run
    logger.info(f"\nThis flow run has URL '{url_for(ctx.flow_run)}'")


@task
def example_task():
    ctx = get_run_context()
    logger = get_run_logger()

    # Calling get_run_context in a task run returns a TaskRunContext object
    logger.info(f"\nContext has type '{type(ctx)}'")


if __name__ == "__main__":
    # Run the example flow from above
    example_flow()

    # Run the example task from above
    example_task()

    # Accessing context outside of a flow run will raise an error
    from prefect.exceptions import MissingContextError

    try:
        get_run_context()
    except MissingContextError as e:
        print(f"Caught MissingContextError: '{e}'")
