# ---
# title: Task Runner Concurrency
# description: Learn how to parallelize your workflows using Prefect's ThreadPoolTaskRunner and task mapping.
# dependencies: ["prefect", "httpx"]
# cmd: ["python", "04_misc/05_task_runner_concurrency.py"]
# tags: [concurrency, task-runners, mapping]
# ---

# ## Thread-based Concurrency with Task Runners
#
# Prefect task runners provide a powerful way to
# execute tasks concurrently without writing async code. This example explores
# **task runners with mapping**.
#
# Prefect offers several task runners for different concurrency needs:
#
# * **ThreadPoolTaskRunner** - Runs tasks in parallel using a pool of threads
# * **DaskTaskRunner** - Distributes tasks across a Dask cluster
# * **RayTaskRunner** - Runs tasks on a Ray cluster
#
# ### Benefits of TaskRunner-based concurrency
#
# Task runners offer many advantages
# over other concurrency approaches:
#
# * **Simplicity**: No need for `async/await` syntax
# * **Compatibility**: Works with any Python libraries, even those that aren't async-ready
# * **Scalability**: Can scale up to multiple cores or even multiple machines
# * **Familiar model**: Uses a thread pool approach common in many programming environments
#
# For an in-depth guide, see Prefect's task-runner documentation:
# <https://docs.prefect.io/v3/develop/task-runners#run-tasks-concurrently-or-in-parallel>
#
# ### When should you use task runners?
# * **CPU-bound or mixed workloads** – Parallelize CPU tasks or synchronous I/O with minimal changes
# * **Non-async libraries** – Gain concurrency when your dependencies don't support async/await
# * **Incremental scaling** – Local threads today, switch to Dask or Ray tomorrow with one parameter change
# * **Task mapping fan-out** – Run thousands of small tasks concurrently while tracking each in the UI
#
# ### Task Mapping: The Secret Weapon
#
# A key feature of this approach is [**task mapping**](https://docs.prefect.io/v3/develop/task-runners#mapping-over-iterables).
# With `.map()`, you can:
#
# 1. Apply a task to each item in a collection concurrently
# 2. Control concurrency via the task runner settings
# 3. Track all executions individually in the Prefect UI
#
# ### Running the example
#
# ```bash
# python 02_sdk_concepts/05_task_runner_concurrency.py
# ```

from typing import Any

import httpx
from prefect import flow, get_run_logger, tags, task, unmapped
from prefect.futures import as_completed
from prefect.task_runners import ThreadPoolTaskRunner

BASE_URL = "https://dev.to/api"
CONCURRENCY = 10


# ## Task Definitions
#
# Unlike the async approach, these tasks are regular synchronous functions.
# The concurrency is managed by the task runner,
# not within the tasks themselves.
# Note the absence of any async/await keywords!


@task(
    retries=3,
    retry_delay_seconds=[10, 30, 60],
)
def fetch_url(url: str, params: dict | None = None) -> dict[str, Any]:
    """Fetch JSON data from a URL.

    This task will automatically retry up to 3 times with increasing delays
    if the request fails. Learn more about [retries in Prefect](https://docs.prefect.io/v3/guides/debugging/#retry-failed-tasks).
    """
    get_run_logger().info(f"Fetching {url}")
    response = httpx.get(url, params=params)
    response.raise_for_status()
    return response.json()


@task
def list_articles(pages: int, per_page: int = 10) -> list[str]:
    """Fetch multiple pages of articles and return a list of article URLs.

    This task demonstrates **task mapping** - one of Prefect's most powerful features:

    1. We call fetch_url.map() to fetch multiple pages in parallel
    2. Each page call runs as an independent task in the thread pool
    3. `.result()` waits for all mapped tasks to complete

    See [task mapping documentation](https://docs.prefect.io/v3/develop/task-map/) for more examples.
    """

    _pages = fetch_url.map(
        unmapped(f"{BASE_URL}/articles"),
        [{"page": page, "per_page": per_page} for page in range(1, pages + 1)],
    ).result()

    return [
        f"{BASE_URL}/articles/{article['id']}" for page in _pages for article in page
    ]


# ## Flow Definition with ThreadPoolTaskRunner
#
# Here's where the magic happens:
#
# 1. We configure a `ThreadPoolTaskRunner` to handle concurrent execution
# 2. The `max_workers=CONCURRENCY` parameter limits the number of concurrent tasks
# 3. We use `.map()` to run `fetch_url` for each article URL concurrently
# 4. We process results as they complete with `as_completed()`


@flow(task_runner=ThreadPoolTaskRunner(max_workers=CONCURRENCY))
def extract(pages: int) -> None:
    """Extract article data from the Dev.to API using thread-based concurrency.

    This flow demonstrates:
    1. Using a ThreadPoolTaskRunner for parallel execution
    2. Task mapping for concise parallel data processing
    3. Processing results as they become available
    """
    article_urls = list_articles(pages)

    _articles = fetch_url.map(article_urls)

    # Log the title of each article as they become ready
    # alternatively, _articles.wait() will wait for all articles
    # We use as_completed to process results as they arrive
    for _article in as_completed(_articles):
        get_run_logger().info(_article.result()["title"])


# ## Comparing with Async Concurrency
#
# The `ThreadPoolTaskRunner` approach differs from the async approach:
#
# | ThreadPoolTaskRunner | Async/Await |
# | -------------------- | ----------- |
# | Regular functions    | Async functions |
# | Thread-based         | Event loop-based |
# | Simple syntax        | Requires async/await |
# | Works with any library | Requires async libraries |
# | Using `.map()`       | Using list comprehensions + `gather()` |
# | More CPU overhead    | Less CPU overhead |
# | Better for mixed I/O and CPU work | Best for pure I/O work |
#
# Read more about concurrency options in Prefect.
#
# Using the right approach depends on your specific requirements.

if __name__ == "__main__":
    with tags("local"):
        extract(pages=10)

# ### What just happened?
#
# When you ran this script:
#
# 1. Prefect created a thread pool with 10 worker threads
# 2. The flow first ran the `list_articles` task to get article URLs
# 3. Within that task, it used mapping to fetch multiple pages in parallel
# 4. Then the flow mapped `fetch_url` over each article URL
# 5. As each article was fetched, the title was logged
# 6. All this happened using standard Python threads, without async code
#
# ### Why This Is Important
#
# Thread-based concurrency in Prefect offers several key advantages:
#
# * **Simplicity**: Write regular Python code but still get concurrency
# * **Flexibility**: Work with any Python library, even if it's not async-compatible
# * **Scaling**: Easily scale to multiple machines by switching to DaskTaskRunner
# * **Monitoring**: Each mapped task gets its own entry in the Prefect UI
# * **Minimal code changes**: Turn sequential code into parallel code with minimal edits
#
