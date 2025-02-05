# /// script
# dependencies = ["prefect"]
# ///

"""
Demonstrates using the client to post-hoc update flow run state using the client.
"""

from uuid import UUID

from prefect import flow, get_client
from prefect.states import State, StateType


def fail_anyway(flow_run_id: UUID):
    with get_client(sync_client=True) as client:
        flow_run = client.read_flow_run(flow_run_id)
        client.set_flow_run_state(
            flow_run_id=flow_run.id,
            state=State(
                type=StateType.FAILED,
                message=f"It's not you {flow_run.parameters['name']}, it's me!",
            ),
            force=True,
        )
        updated_flow_run = client.read_flow_run(flow_run_id)
        assert (
            updated_flow_run.state and updated_flow_run.state.type == StateType.FAILED
        ), "Flow run state was not updated to failed"


@flow(log_prints=True)
def hello(name: str = "Marvin"):
    print(f"Hello, {name}!")


if __name__ == "__main__":
    state = hello(return_state=True)
    assert state.state_details.flow_run_id is not None, "Flow run ID is None"
    fail_anyway(state.state_details.flow_run_id)
