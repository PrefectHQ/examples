# Prefect examples

Examples for [Prefect](https://docs.prefect.io) and Prefect Cloud.

| Folder | What goes here |
| --- | --- |
| `getting-started/` | First-run examples that the Prefect docs render as pages |
| `integrations/<tool>/` | Prefect with one other tool (dbt, Snowflake, dlt, ...) |
| `apps/<name>/` | Reference applications, such as background tasks behind a web API |

Every example follows the [example contract](../internal/example-contract.md) and is listed in [`CATALOG.yaml`](../CATALOG.yaml).

> The existing Prefect examples in `examples/`, `flows/`, `deploy/`, `scripts/` and `apps/` move here in phase 2 of the consolidation. `flows/hello_world.py` and `flows/whoami.py` stay where they are until the repos that load them are updated; see [`internal/DOWNSTREAM.md`](../internal/DOWNSTREAM.md).
