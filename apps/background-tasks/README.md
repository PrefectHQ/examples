# background tasks with `prefect`, `fastapi` & `htmx`

A demonstration project showcasing how to use Prefect to manage background tasks triggered from a FastAPI web application with an HTMX frontend. Specifically, this example uses [marvin](https://github.com/PrefectHQ/marvin) to cast unstructured data based on user input, but you can mentally replace the background task definition with any potentially long-running python function that is unsuitable for a direct web request-response cycle.

## technologies

*   `fastapi`: For our web server API
*   `prefect`: For defining, submitting, orchestrating, and observing the background task
*   [`htmx`](https://htmx.org/): For a minimal grug-brained frontend
*   `marvin`: The library performing the core work within the Prefect task
*   `docker` & `docker-compose`: For containerizing and running the application services

## how it works

This example demonstrates a common pattern for running background tasks in a web application using Prefect:

1.  **Trigger:** A user interacts with the web frontend (FastAPI + HTMX), initiating an API request.
2.  **`@task` Definition:** A Python function (`cast_data_to_type` in `task.py`) is decorated with `@prefect.task`. This marks it as a Prefect-managed unit of work.
3.  **Defer Task Execution:** The API endpoint calls `.delay()` on the task function instead of running it directly. This submits the task as a **Task Run** to the Prefect API (running in the `prefect-server` service) and immediately returns a future-like object containing the `task_run_id`. This is crucial for keeping the web request non-blocking.
4.  **Task Execution:** A separate Prefect **Task Worker** process (in the `task` service) picks up submitted task runs from the Prefect API and executes the actual Python function.
5.  **Status Checking & Results:** The web application uses the received `task_run_id` to periodically poll a status endpoint. This endpoint uses the Prefect **Client** (`prefect.client.orchestration.get_client`) to query the Prefect API for the task run's state (`Pending`, `Running`, `Completed`, `Failed`).
6.  **Storing & Retrieving Results:** Once the task run reaches a `Completed` state, the status endpoint uses `task_run.state.result()` to retrieve the return value. You can configure result persistence via environment variables like `PREFECT_RESULTS_PERSIST_BY_DEFAULT` and `PREFECT_LOCAL_STORAGE_PATH` (the former enables result persistence by default, the latter specifies the path to store results).
7.  **UI Update:** The final status (success or failure) and any results or error messages are sent back to the UI.

## Setup and Running

1.  **Prerequisites:**
    *   Docker Desktop or similar with `docker compose` support
    *   `git`
2.  **Clone Repository:**
    ```bash
    git clone https://github.com/PrefectHQ/examples
    cd examples/apps/background-tasks
    ```
3.  **Configure Secrets:**
    *   Create a file named `.env` in the project root directory.
    *   Add the required secrets/environment variables. For this project, you need:
        ```dotenv
        # .env
        OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
        ```
    *   The `compose.yaml` file is configured to automatically load variables from this `.env` file.
4.  **Build and Run Services:**
    ```bash
    docker compose up --build -d
    ```
    *   `--build`: Builds the container images based on the `Dockerfile`.
    *   `-d`: Runs the containers in detached mode (in the background).
5.  **Access the Application:**
    *   Web UI: [http://localhost:8000](http://localhost:8000)
    *   Prefect UI: [http://localhost:4200](http://localhost:4200) (To observe task runs, logs, etc.)

## Stopping the Application

```bash
docker compose down
```
*   Use `docker compose down -v` to also remove the named volumes (Prefect data, task storage) if you want a completely clean restart.