"""
Demonstrates using the client to update flow run tags.
"""

from prefect import flow, get_run_logger, get_client, tags
from prefect.context import get_run_context


@flow
def hello(name: str = "Marvin"):
    logger = get_run_logger()

    # Log metadata about the flow run
    ctx = get_run_context()
    logger.info(f"Flow run has ID '{ctx.flow_run.id}'")
    logger.info(f"Flow run has tags {ctx.flow_run.tags}")

    # Update the flow run tags
    with get_client(sync_client=True) as client:
        client.update_flow_run(
            flow_run_id=get_run_context().flow_run.id,
            tags=[
                # Keep existing tags
                *ctx.flow_run.tags,
                f"name:{name}",
            ],
        )

    # Log a message
    logger.info(f"Hello, {name}!")


if __name__ == "__main__":
    # Add the tag "local" to show that update_flow_run doesn't overwrite
    with tags("local"):
        hello("Arthur")
