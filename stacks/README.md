# Stacks

Examples that use more than one product together, for example a Dagster pipeline that feeds a FastMCP server orchestrated by Prefect. Each stack is one folder: `stacks/<name>/`.

Set `product` to every product the stack uses, for example `product: [prefect, fastmcp]`.

Every example follows the [example contract](../internal/example-contract.md) and is listed in [`CATALOG.yaml`](../CATALOG.yaml).
