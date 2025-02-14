# /// script
# dependencies = ["prefect"]
# ///

"""
This script lists flow run counts by state and date for all workspaces in an account.

The output can be piped to a CSV file for further analysis. For example:
```bash
uv run --python 3.12 --with prefect python scripts/cross_workspace_flow_runs.py -a $ACCOUNT_ID > flow-runs.csv

uvx duckdb -c "select state, sum(flow_runs) from read_csv('./flow-runs.csv') group by 1 order by 2 desc"
```
"""

import asyncio
import pendulum
import typer
from prefect.client.cloud import get_cloud_client


STATES = [
    "SCHEDULED",
    "PENDING",
    "RUNNING",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
    "CRASHED",
    "PAUSED",
    "CANCELLING",
]


async def get_flow_runs(
    semaphore,
    client,
    account_id: str,
    workspace: dict,
    state: str,
    start_date: str,
    end_date: str,
):
    async with semaphore:
        response = await client.request(
            "POST",
            f"/accounts/{account_id}/workspaces/{workspace['id']}/flow_runs/count",
            json={
                "flow_runs": {
                    "state": {"type": {"any_": [state]}},
                    "expected_start_time": {"after_": start_date, "before_": end_date},
                }
            },
        )
        print(
            f"{account_id},{workspace['id']},{workspace['name']},{state},{start_date},{end_date},{response}"
        )


async def _list_flow_runs(account_id: str, days: int = 7):
    futures = []
    # Use a semaphore to limit the number of concurrent requests
    semaphore = asyncio.BoundedSemaphore(10)

    async with get_cloud_client() as client:
        workspaces = await client.request(
            "POST", f"/accounts/{account_id}/workspaces/filter"
        )

        # Workspaces x States x Day
        print(
            "account_id,workspace_id,workspace_handle,state,start_date,end_date,flow_runs"
        )
        for workspace in workspaces:
            for state in STATES:
                for day in range(1, days):
                    start_date = (
                        pendulum.now(tz="UTC")
                        .subtract(days=day)
                        .start_of("day")
                        .isoformat()
                    )
                    end_date = (
                        pendulum.now(tz="UTC")
                        .subtract(days=day - 1)
                        .start_of("day")
                        .isoformat()
                    )

                    futures.append(
                        get_flow_runs(
                            semaphore,
                            client,
                            account_id,
                            workspace,
                            state,
                            start_date,
                            end_date,
                        )
                    )

        await asyncio.gather(*futures)


def list_flow_runs(
    account_id: str = typer.Option(
        ...,
        "-a",
        "--account-id",
        help="The account ID to list flow runs for",
    ),
    days: int = typer.Option(
        7,
        "-d",
        "--days",
        help="The number of days to list flow runs for",
    ),
):
    asyncio.run(_list_flow_runs(account_id=account_id, days=days))


if __name__ == "__main__":
    typer.run(list_flow_runs)
