"""
Update a deployment's concurrency limit via the API. This is a workaround
for instances where Prefect 2.x is installed and models do not directly support
updating the concurrency limit.
"""

import uuid

import typer
from prefect import get_client


def main(
    deployment_id: uuid.UUID, limit: int | None = None, strategy: str = "CANCEL_NEW"
):
    with get_client(sync_client=True) as client:
        client._client.patch(
            f"/deployments/{deployment_id}",
            json={
                "concurrency_limit": limit,
                "concurrency_options": {"collision_strategy": strategy},
            },
        )


if __name__ == "__main__":
    typer.run(main)
