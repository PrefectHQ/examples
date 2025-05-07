from pathlib import Path
from prefect import flow


@flow
def hello_world():
    print("Hello, world!")


if __name__ == "__main__":
    hello_world.from_source(
        source=Path(__file__).parent,
        entrypoint="source_local.py:hello_world",
    ).deploy(
        name="deploy-local-storage",
        work_pool_name="local",
    )

# prefect deployment run 'hello-world/deploy-local-storage'

# prefect worker start --pool 'local'
