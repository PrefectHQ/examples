"""
Create a Prefect automation that sends a notification when a flow run fails.
"""

import asyncio

from prefect.automations import Automation
from prefect.blocks.core import Block
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import BlockDocumentCreate
from prefect.events.actions import SendNotification
from prefect.events.schemas.automations import EventTrigger
from prefect.exceptions import ObjectNotFound


async def create_cloud_block(
    block_type_slug: str, block_name: str, data: dict, overwrite: bool = False
):
    """
    Prefect Cloud blocks cannot be represented with a Block class, but we can
    create them using the API client. Some of the methods are only available
    in the async client.
    """
    async with get_client() as client:
        # Handle case where block already exists
        try:
            block = await client.read_block_document_by_name(
                name=block_name,
                block_type_slug=block_type_slug,
            )
            print(f"Block {block_type_slug}/{block_name} already exists...")
            if overwrite:
                print(f"Deleting block {block_type_slug}/{block_name}...")
                await client.delete_block_document(block.id)
            else:
                return block
        except ObjectNotFound:
            pass

        # Get the block type and schema data
        block_type = await client.read_block_type_by_slug(block_type_slug)
        block_schema = await client.get_most_recent_block_schema_for_block_type(
            block_type.id
        )

        # Create the block
        block = await client.create_block_document(
            block_document=BlockDocumentCreate(
                name=block_name,
                data=data,
                block_schema_id=block_schema.id,
                block_type_id=block_type.id,
            )
        )
        print(f"Created block {block_type_slug}/{block_name}")
        return block


def create_automation(name: str, block: Block, overwrite: bool = False):
    # Handle case where automation already exists
    try:
        automation = Automation.read(name=name)
        print(f"Automation {name} already exists")
        if overwrite:
            print(f"Deleting automation {name}...")
            automation.delete()
        else:
            return automation
    except ValueError:
        pass

    # Create the automation
    automation = Automation(
        name=name,
        trigger=EventTrigger(
            expect=["prefect.flow-run.Failed", "prefect.flow-run.Crashed"],
            for_each=["prefect.resource.id"],
            match={
                "prefect.resource.id": "prefect.flow-run.*",
            },
            posture="Reactive",
            threshold=1,
        ),
        actions=[
            SendNotification(
                block_document_id=block.id,
                subject="Flow run failed",
                body="{{ flow.name }}/{{ flow_run.name }} observed in state `{{ flow_run.state.name }}`. Link: {{ flow_run|ui_url }}",
            )
        ],
    )
    automation.create()
    print(f"Created automation {name}")
    return automation


if __name__ == "__main__":
    # Create the block
    block = asyncio.run(
        create_cloud_block(
            "email",
            "flow-failure-emails",
            data={
                "emails": ["me@example.com"],
            },
            overwrite=True,
        )
    )

    # Create the automation
    automation = create_automation(
        "notify-on-failure",
        block,
        overwrite=True,
    )
