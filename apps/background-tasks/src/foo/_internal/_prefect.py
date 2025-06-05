from typing import Any, Literal, cast
from uuid import UUID

from prefect.client.orchestration import get_client
from prefect.client.schemas.objects import TaskRun
from prefect.logging import get_logger

logger = get_logger(__name__)

Status = Literal["completed", "pending", "error"]


def _any_task_run_result(task_run: TaskRun) -> Any:
    try:
        return cast(Any, task_run.state.result(_sync=True))  # type: ignore
    except Exception as e:
        logger.warning(f"Could not retrieve result for task run {task_run.id}: {e}")
        return None


async def get_task_result(task_run_id: UUID) -> tuple[Status, Any]:
    """Get task result or status.

    Returns:
        tuple: (status, data)
            status: "completed", "pending", or "error"
            data: the result if completed, error message if error, None if pending
    """
    try:
        async with get_client() as client:
            task_run = await client.read_task_run(task_run_id)
            if not task_run.state:
                return "pending", None

            if task_run.state.is_completed():
                try:
                    result = _any_task_run_result(task_run)
                    return "completed", result
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve result for completed task run {task_run_id}: {e}"
                    )
                    return "completed", "<Could not retrieve result>"

            elif task_run.state.is_failed():
                try:
                    error_result = _any_task_run_result(task_run)
                    error_message = (
                        str(error_result)
                        if error_result
                        else "Task failed without specific error message."
                    )
                    return "error", error_message
                except Exception as e:
                    logger.warning(
                        f"Could not retrieve error result for failed task run {task_run_id}: {e}"
                    )
                    return "error", "<Could not retrieve error message>"

            else:
                return "pending", None

    except Exception as e:
        logger.error(f"Error checking task status for {task_run_id}: {e}")
        return "error", f"Failed to check task status: {str(e)}"
