"""
Deploy a flow in an existing Docker image from inside the image

Suppose you have the following Dockerfile:

```dockerfile
FROM prefecthq/prefect:3-latest
COPY flows/hello-world.py /opt/custom/path/to/hello-world.py
```

Which you build as follows:

```bash
docker build -f Dockerfile -t flow-hello-world:latest .
```

Then you can deploy the flow from inside the image:

```bash
export PREFECT_API_URL=`python -c "from prefect.settings import PREFECT_API_URL as x; print(x.value())"`
export PREFECT_API_KEY=`python -c "from prefect.settings import PREFECT_API_KEY as x; print(x.value())"`

docker run -it --rm \
    -v $(pwd)/deploy/deploy-docker-in-docker.py:/tmp/deploy-docker-in-docker.py \
    -e PREFECT_API_URL=$PREFECT_API_URL \
    -e PREFECT_API_KEY=$PREFECT_API_KEY \
    flow-hello-world:latest \
    python /tmp/deploy-docker-in-docker.py /opt/custom/path/to/hello-world.py:hello
```
"""

import typer
from prefect import flow


def deploy(entrypoint: str):
    _flow = flow.from_source(
        source="/",
        entrypoint=entrypoint,
    )

    # Deploy the flow
    _flow.deploy(
        name="source-docker-existing-image",
        work_pool_name="docker",
        image="flow-hello-world:latest",
        # No need to build or push the image
        build=False,
        push=False,
        # Ensure we don't attempt to pull the image from any registry
        job_variables={
            "image_pull_policy": "Never",
        },
    )


if __name__ == "__main__":
    typer.run(deploy)
