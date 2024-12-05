"""
# Deploy a flow using Docker

This example shows how to deploy a flow in a Prefect built Docker image.
It assumes you have a work pool named `docker`. You can implicitly create the
work pool by starting a worker:

```bash
prefect worker start --pool docker --type docker
```
"""

import subprocess

from prefect import flow
from prefect.docker import DockerImage

REGISTRY_URL = ""
IMAGE_NAME = "flow-hello-world"


def get_image_tag():
    """Return the current git sha if available else latest"""
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("utf-8")
            .strip()
        )
    except subprocess.CalledProcessError:
        return "latest"


def deploy():
    flow.from_source(
        source="./flows",
        entrypoint="hello-world.py:hello",
    ).deploy(
        name="source-docker",
        # The name of the work pool to use for this deployment
        work_pool_name="docker",
        image=DockerImage(
            name=f"{REGISTRY_URL}/{IMAGE_NAME}" if REGISTRY_URL else IMAGE_NAME,
            # Tagging the image with the current git sha is a good way to track
            # which version of the code is deployed
            tag=get_image_tag(),
            # Autogenerate a Dockerfile based on the installed Prefect version
            # This pulls in requirements.txt if present
            dockerfile="auto",
            # When building on an M series Mac and deploying to a cloud provider,
            # we generally need to specify the platform.
            platform="linux/amd64",
        ),
        # Build the image before pushing it to the registry
        build=True,
        # Only push if we have a registry URL
        push=True if REGISTRY_URL else False,
        # Override work pool defaults with job variables
        # For example, avoid pulling from the registry if we're building locally
        job_variables={
            "pull_policy": "Always" if REGISTRY_URL else "Never",
        },
    )


if __name__ == "__main__":
    deploy()
