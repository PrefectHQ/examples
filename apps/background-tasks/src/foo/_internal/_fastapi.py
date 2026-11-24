from typing import Annotated, Any, cast

from fastapi import Form
from pydantic import BaseModel, Field, ImportString
from pydantic_core import from_json

from prefect.logging import get_logger

logger = get_logger(__name__)


class StructuredOutputRequest(BaseModel):
    payload: dict[str, Any] = Field(
        ..., description="The payload to be cast to a structured output"
    )
    instructions: str = Field(
        ..., description="The instructions for the structured output"
    )
    target_type: ImportString[type] = Field(
        ..., description="The type to cast the payload to"
    )


def get_form_data(
    payload: Annotated[str, Form()],
    instructions: Annotated[str, Form()],
    target_type: Annotated[str, Form()],
) -> StructuredOutputRequest:
    try:
        payload_dict = from_json(payload)
    except ValueError as e:
        logger.error(f"Error parsing payload: {e}")
        payload_dict = {"data": payload}

    return StructuredOutputRequest(
        payload=payload_dict,
        instructions=instructions,
        target_type=cast(ImportString[type], target_type),
    )
