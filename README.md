# Prefect Examples

This repository contains examples that demonstrate how to use Prefect. The example are intended to be starting points rather than complete solutions. We hope you find them useful!

## Running these examples

> [!IMPORTANT]
> This repository uses [uv](https://docs.astral.sh/uv/) for Python environment management.

If you've cloned the repository, you can run any of the examples with `uv run flows/<example_name>.py`, for example:

```bash
uv run flows/hello_world.py
```

If you haven't, you can point `uv run` at the URL of the Python file, for example:

```bash
uv run https://raw.githubusercontent.com/PrefectHQ/examples/refs/heads/main/flows/hello_world.py
```

> [!IMPORTANT]
> If you're not using Prefect Cloud, using deployment/scheduling functionality requires a Prefect server.

You can run a server locally:

```bash
uvx prefect server start
```

or instead in a docker container:

```bash
docker run -p 4200:4200 -d --rm prefecthq/prefect:3-latest -- prefect server start --host 0.0.0.0
```




