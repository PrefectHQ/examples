"""
Get the registered versions of each block type in a workspace.

This can be helpful to identify older block types.
"""

import asyncio

from prefect.client.orchestration import get_client

# Rich is already installed as dependency of prefect
from rich.console import Console
from rich.table import Table


async def main():
    table = Table(
        title="Installed Block Types",
        show_header=True,
        show_footer=False,
        show_lines=True,
        expand=True,
    )
    table.add_column("No")
    table.add_column("Slug")
    table.add_column("Version")
    table.add_column("Created")
    table.add_column("Updated")
    table.add_column("Checksum")

    async with get_client() as client:
        block_types = await client.read_block_types()
        block_types = sorted(block_types, key=lambda x: x.slug)

        _futures = []
        for idx, block_type in enumerate(block_types):
            _futures.append(
                client.get_most_recent_block_schema_for_block_type(
                    block_type_id=block_type.id
                )
            )

        for idx, block_schema in enumerate(await asyncio.gather(*_futures)):
            table.add_row(
                str(idx + 1),
                block_schema.block_type.slug,
                block_schema.version,
                str(block_schema.created),
                str(block_schema.updated),
                block_schema.checksum,
            )

    console = Console()
    console.print(table)


if __name__ == "__main__":
    asyncio.run(main())
