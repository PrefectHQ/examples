import os
from fastapi.staticfiles import StaticFiles
from uuid import UUID

from fastapi import Depends, FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from foo._internal import get_form_data, get_task_result, StructuredOutputRequest
from foo.task import create_structured_output
from prefect.logging import get_logger

app = FastAPI()

static_dir = "src/foo/static"
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

templates = Jinja2Templates(directory="src/foo/templates")

logger = get_logger(__name__)


@app.get("/")
async def read_root(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def produce_structured_output_from_form(
    request: Request,
    form_data: StructuredOutputRequest = Depends(get_form_data),
) -> HTMLResponse:
    future = create_structured_output.delay(  # type: ignore
        form_data.payload,
        target=form_data.target_type,
        instructions=form_data.instructions,
    )

    return templates.TemplateResponse(
        "partials/result.html",
        {"request": request, "task_run_id": future.task_run_id},
    )


@app.get("/task/{task_run_id}/status")
async def get_task_status(request: Request, task_run_id: UUID) -> HTMLResponse:
    """Check if a task result is available and return its status."""
    status, data = await get_task_result(task_run_id)

    return templates.TemplateResponse(
        "partials/task_status.html",
        {
            "request": request,
            "task_run_id": task_run_id,
            "status": status,
            "result": data if status == "completed" else None,
            "message": data if status == "error" else None,
        },
    )
