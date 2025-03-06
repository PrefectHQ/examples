# /// script
# dependencies = ["prefect"]
# ///

"""
Example of bulk updating flow run states.
"""

from __future__ import annotations

import asyncio

import typer

# TODO: https://github.com/PrefectHQ/prefect/issues/15957#issuecomment-2565751830
import prefect.main  # noqa: F401

from prefect.client.orchestration import get_client
from prefect.client.schemas import State, StateType, FlowRun
from prefect.client.schemas.responses import SetStateStatus
from prefect.client.schemas.filters import (
    FlowRunFilter,
    FlowRunFilterExpectedStartTime,
    FlowRunFilterState,
    FlowRunFilterStateType,
)
from prefect.types import DateTime

LIMIT = 100


async def list_flow_runs_with_state(
    states: list[StateType], before: DateTime, after: DateTime
) -> list[FlowRun]:
    offset = 0
    more_results = True
    flow_runs = []

    async with get_client() as client:
        while more_results:
            batch = await client.read_flow_runs(
                flow_run_filter=FlowRunFilter(
                    state=FlowRunFilterState(type=FlowRunFilterStateType(any_=states)),
                    expected_start_time=FlowRunFilterExpectedStartTime(
                        before_=before,
                        after_=after,
                    ),
                ),
                limit=LIMIT,
                offset=offset,
            )

            if not batch:
                more_results = False
            else:
                flow_runs.extend(batch)
                offset += len(batch)

                # If we got fewer results than the limit, we've reached the end
                if len(batch) < LIMIT:
                    more_results = False

    return flow_runs


async def update_flow_run_state(
    flow_run: FlowRun,
    to_state: StateType,
    message: str | None = None,
    force: bool = False,
) -> tuple[bool, dict]:
    """Update a flow run's state and return success status and result data."""
    async with get_client() as client:
        response = await client.set_flow_run_state(
            flow_run_id=flow_run.id,
            state=State(
                type=to_state,
                message=message,
            ),
            force=force,
        )

        success = response.status == SetStateStatus.ACCEPT

        if success:
            print(
                f"Updated flow run '{flow_run.name}' with ID '{flow_run.id}' to state {to_state.name}"
            )
        else:
            print(
                f"Failed to update flow run '{flow_run.name}' with ID '{flow_run.id}' to state {to_state.name}"
            )
            if response.details:
                print(f"Details: {response.details}")

        # Return both success status and the full response data
        return success, {"status": response.status, "details": response.details}


async def _bulk_update_flow_run_state(
    from_states: list[StateType],
    to_state: StateType,
    before: DateTime,
    after: DateTime,
    message: str | None = None,
    force: bool = False,
):
    flow_runs = await list_flow_runs_with_state(from_states, before, after)

    # NOTE: this won't work if flow_runs is a generator
    if len(flow_runs) == 0:
        print(
            f"There are no flow runs in state(s) {[state.name for state in from_states]}"
        )
        return

    print(
        f"There are {len(flow_runs)} flow runs with state(s) {[state.name for state in from_states]}\n"
    )
    for flow_run in flow_runs:
        print(f"[{flow_run.id}] {flow_run.state.name} - {flow_run.name}")

    # Obtain user confirmation
    if input("\n[Y/n] Do you wish to proceed: ") != "Y":
        print("Aborting...")
        return

    # Use asyncio.gather to properly await all update tasks
    tasks = []
    for flow_run in flow_runs:
        tasks.append(
            update_flow_run_state(
                flow_run=flow_run, to_state=to_state, message=message, force=force
            )
        )

    results = await asyncio.gather(*tasks)

    # Count successful updates and collect result data
    success_count = sum(result[0] for result in results)
    result_data = [result[1] for result in results]

    print(f"\nUpdated {success_count} of {len(flow_runs)} flow runs")

    # Return the results for potential further processing
    return result_data


# Use the actual enum of states from Prefect
def bulk_update_flow_run_state(
    from_states: list[StateType] = typer.Option(
        ...,
        "--from",
        help="State(s) to update from. Can be specified multiple times.",
    ),
    to_state: StateType = typer.Option(
        ...,
        "--to",
        help="State to update to.",
    ),
    message: str | None = typer.Option(
        None,
        "--message",
        help="Optional message to set on the flow run state.",
    ),
    force: bool = typer.Option(
        False,
        "-f",
        "--force",
        help="Force the update if the from state is terminal.",
    ),
    days_ago: int = typer.Option(
        30,
        "--days-ago",
        help="Only consider flow runs from this many days ago until now.",
    ),
):
    """
    Bulk update flow run states from one state to another.

    This command will find all flow runs in the specified state(s) and update them
    to the target state. It will prompt for confirmation before making any changes.
    """
    # Calculate date range based on days_ago
    now = DateTime.now()
    after = now.subtract(days=days_ago)

    asyncio.run(
        _bulk_update_flow_run_state(
            from_states=from_states,
            to_state=to_state,
            before=now,
            after=after,
            message=message,
            force=force,
        )
    )


if __name__ == "__main__":
    typer.run(bulk_update_flow_run_state)
