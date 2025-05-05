---
deploy: true
cmd: ["prefect", "deployment", "build", "01_getting_started/01_hello_world.py:hello_world", "-n", "hello-world", "-q", "default"]
description: A simple Hello World flow to demonstrate Prefect
tags: ["getting-started", "basic"]
---
from prefect import flow, task


@task
def get_name():
    return "World"


@flow(name="Hello Flow")
def hello_world():
    name = get_name()
    print(f"Hello {name}!")
    return f"Hello {name}!"


if __name__ == "__main__":
    hello_world()
