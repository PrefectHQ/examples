# /// script
# dependencies = ["prefect"]
# ///

"""
An example of discovering and deploying multiple flows from a directory.

The interesting bits are:
1. Our `deploy_flow` function is simple, but this is where you can really go crazy defining a standard pattern.
2. We use `OVERRIDES` to define the inevitable deviations from our standard pattern.
3. Prefect's built-in `_search_for_flow_functions` does the heavy lifting of identifying flows in files.
4. We wrap the whole thing in a CLI with some logic around inclusion and exclusion of files.
"""

import asyncio
from pathlib import Path

import typer
from prefect import __version__, flow

# NOTE: The import path changed in 3.1.11
if tuple(map(int, __version__.split("."))) < (3, 1, 11):
    from prefect.deployments.base import _search_for_flow_functions
else:
    from prefect.cli._prompts import (
        search_for_flow_functions as _search_for_flow_functions,
    )

from prefect.runner.storage import GitRepository

# Optional overrides for each flow as identified by the entrypoint
# In practice you might define these in a config file or something
OVERRIDES: dict[str, dict] = {
    "flows/hello-world.py:hello": {
        "parameters": {"name": "World(s)"},
    }
}

# Maximum number of flows to deploy concurrently
# Currently flow.from_source does not appear threadsafe
# https://github.com/PrefectHQ/prefect/issues/16452
MAX_CONCURRENCY = 1


async def deploy_flow(entrypoint: str, semaphore: asyncio.BoundedSemaphore):
    """
    Deploy the flow with common settings.
    """
    try:
        async with semaphore:
            _flow = await flow.from_source(
                source=GitRepository(
                    url="https://github.com/PrefectHQ/examples.git",
                ),
                entrypoint=entrypoint,
            )
            deployment_id = await _flow.deploy(
                name="deploy-many",
                work_pool_name="process",
                **OVERRIDES.get(entrypoint, {}),
            )
        print(f"Deployed flow {entrypoint} with deployment ID {deployment_id}")
    except Exception as e:
        print(f"Error deploying flow {entrypoint}")
        return e


async def filter_flow_functions(
    flow_functions: list[dict], include: list[str] = None, exclude: list[str] = None
) -> list[dict]:
    """
    Filter the flow functions based on the include and exclude options.
    """
    available = set([f["filepath"] for f in flow_functions])
    if include:
        missing = set(include) - available
        if any(missing):
            raise ValueError(
                f"The following included files were not found: {', '.join(str(m) for m in missing)}"
            )
        deployable = set(include)
    elif exclude:
        deployable = available - set(exclude)
    else:
        deployable = available

    return [f for f in flow_functions if f["filepath"] in deployable]


async def _deploy(
    path: Path = Path("./flows"), include: list[str] = None, exclude: list[str] = None
):
    """
    Search for flow functions in the specified directory and deploy each one.
    """
    flow_functions = await _search_for_flow_functions(path)

    # Handle no flows found
    if not flow_functions:
        print("No flow functions found in the specified directory.")
        return

    deployable = await filter_flow_functions(flow_functions, include, exclude)

    # Concurrency control
    semaphore = asyncio.BoundedSemaphore(MAX_CONCURRENCY)

    print(f"Deploying {len(deployable)} flows.")
    _deployments = []
    for flow_function in deployable:
        # Load and deploy the flow
        print(
            f"Deploying flow {flow_function['function_name']} from {flow_function['filepath']}"
        )
        _deployment = deploy_flow(
            entrypoint=f"{flow_function['filepath']}:{flow_function['function_name']}",
            semaphore=semaphore,
        )
        _deployments.append(_deployment)

    # Wait for all deployments to complete
    results = await asyncio.gather(*_deployments)

    # Summarize the results
    for idx, (flow_function, result) in enumerate(zip(deployable, results)):
        if isinstance(result, Exception):
            print(
                f"[{idx + 1}] ❌ {flow_function['filepath']}:{flow_function['function_name']}: {result}"
            )
        else:
            print(
                f"[{idx + 1}] ✅ {flow_function['filepath']}:{flow_function['function_name']}"
            )


def deploy(
    path: Path = typer.Argument(
        Path("./flows"),
        help="Directory path containing flow files to deploy",
    ),
    include: list[str] = typer.Option(
        None,
        "-i",
        "--include",
        help="Optional list of file names to include. If provided, only these files will be deployed",
    ),
    exclude: list[str] = typer.Option(
        None,
        "-e",
        "--exclude",
        help="Optional list of file names to exclude. If provided, these files will be skipped",
    ),
):
    if include and exclude:
        raise typer.BadParameter("Please provide either include or exclude, not both")

    asyncio.run(_deploy(path=path, include=include, exclude=exclude))


if __name__ == "__main__":
    typer.run(deploy)
