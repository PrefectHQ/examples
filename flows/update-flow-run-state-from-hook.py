"""
Demonstrates using the client to update flow run state from a hook.
"""

from prefect import flow, get_client, get_run_logger
from prefect.client.schemas import State, StateType


def fail_anyway(flow, flow_run, state):
    with get_client(sync_client=True) as client:
        client.set_flow_run_state(
            flow_run_id=flow_run.id,
            state=State(
                type=StateType.FAILED,
                message=f"It's not you {flow_run.parameters['name']}, it's me!",
            ),
            force=True,
        )


@flow(on_completion=[fail_anyway])
def hello(name: str = "Marvin"):
    get_run_logger().info(f"Hello, {name}!")


if __name__ == "__main__":
    hello()
