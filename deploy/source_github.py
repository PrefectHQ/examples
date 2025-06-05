# /// script
# dependencies = ["prefect"]
# ///

"""
# Deploy a flow from a git repository

This example shows how to deploy a flow from a git repository.
It assumes you have a work pool named `process`. You can implicitly create the
work pool by starting a worker:

```bash
prefect worker start --pool process --type process
```
"""

from prefect import flow
from prefect.blocks.system import Secret
from prefect.client.schemas.schedules import CronSchedule
from prefect.runner.storage import GitRepository


def deploy():
    # flow.from_source will actually clone the repository to load the flow
    flow.from_source(
        # Here we are using GitHub but it works for GitLab, Bitbucket, etc.
        source=GitRepository(
            url="https://github.com/PrefectHQ/examples.git",
            credentials={
                # We are assuming you have a Secret block named `github-access-token`
                # that contains your GitHub personal access token
                "access_token": Secret.load("github-access-token"),
            },
        ),
        entrypoint="flows/hello-world.py:hello",
    ).deploy(
        name="source-github",
        schedules=[
            # Run the flow every hour on the hour
            CronSchedule(cron="0 * * * *"),
        ],
        work_pool_name="process",
        # Define a different default parameter for this deployment
        parameters={
            "name": "Arthur",
        },
    )


if __name__ == "__main__":
    deploy()
