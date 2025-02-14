# /// script
# dependencies = ["prefect"]
# ///

"""
Deploy a flow using an existing Docker image that contains your flow

Suppose you have the following Dockerfile:

```dockerfile
FROM prefecthq/prefect:3-latest
COPY flows/hello-world.py /opt/custom/path/to/hello-world.py
```

Which you build as follows:

```bash
docker build -f Dockerfile -t flow-hello-world:latest .
```

Then run this script and start a worker:

```bash
python deploy/deploy_docker_existing_image.py
prefect worker start --pool docker --type docker
```
"""

from prefect import flow, deploy
from prefect.runner.storage import LocalStorage

# Location of the flow in your local filesystem
LOCAL_PATH = "./flows"
LOCAL_ENTRYPOINT = "hello-world.py:hello"

# Location of the flow in the image's filesystem
IMAGE_PATH = "/opt/custom/path/to/"
IMAGE_ENTRYPOINT = "hello-world.py:hello"


def main():
    # Load the flow from the local filesystem
    # Alternatively you could import the flow directly
    _flow = flow.from_source(
        source=LOCAL_PATH,
        entrypoint=LOCAL_ENTRYPOINT,
    )

    # Create a deployment from the flow
    _deployment = _flow.to_deployment(
        name="source-docker-existing-image",
        job_variables={"image_pull_policy": "Never"},
        work_pool_name="docker",
    )

    # Overwrite the path and entrypoint to match the image
    _deployment.storage = LocalStorage(path=IMAGE_PATH)
    _deployment.entrypoint = IMAGE_ENTRYPOINT

    # Deploy the flow
    deployment_ids = deploy(
        _deployment,
        image="flow-hello-world:latest",
        build=False,
        push=False,
        work_pool_name="docker",
        # Reduce the amount of logging output
        print_next_steps_message=False,
    )

    print(f"Deployment created with ID: '{deployment_ids[0]}'")


if __name__ == "__main__":
    main()
