# ---
# title: Concurrency in Prefect
# description: Learn how to execute tasks concurrently using Python's async/await or Prefect's task runners.
# dependencies: ["prefect", "httpx"]
# cmd: ["python", "04_misc/05_async_concurrency.py"]
# tags: [concurrency, async, tasks]
# ---

# ## Scaling Up: Concurrent Execution in Prefect
#
# Data engineering often requires processing many items simultaneously for efficiency.
# Prefect offers multiple approaches to concurrency:
#
# 1. **Native Python async/await** - Leverage Python's built-in asynchronous capabilities
# 2. **Task runners** - Use Prefect's `ThreadPoolTaskRunner` or `DaskTaskRunner`
#
# In this example, we'll focus on the async/await approach, which excels at I/O-bound
# operations like API calls, database queries, and network requests.
#
# ### Benefits of async concurrency
#
# * **Performance**: Process multiple items concurrently without full threads
# * **Control**: Fine-grained control over concurrency limits
# * **Integration**: Works with async libraries like `httpx`, `asyncpg`, etc.
# * **Scalability**: Handle thousands of concurrent operations efficiently
#
# For more details on async and concurrency in Prefect, see the official documentation:
# <https://docs.prefect.io/v3/develop/write-tasks#asynchronous-functions>
#
# ### When should you use async concurrency?
# * **I/O-bound operations** – Fetch many API endpoints or perform network requests in parallel
# * **High-latency tasks** – Await slow cloud services or external databases while keeping workers free
# * **Rate-limited APIs** – Control concurrent requests with semaphores to stay within provider limits
# * **Large fan-out workloads** – Crawl or scrape thousands of URLs concurrently without spawning threads
#
# ### The task at hand
#
# We'll build a flow that extracts articles from the Dev.to API concurrently:
#
# 1. First, we'll fetch multiple pages of article listings in parallel
# 2. Then, we'll fetch the full details of each article in parallel
# 3. All while controlling our concurrency to avoid overwhelming the API
#
# ### Running the example
#
# ```bash
# python 02_sdk_concepts/04_async_concurrency.py
# ```
#
# Note: This example requires Python 3.7+ and the `httpx` library.

import asyncio

import httpx
from prefect import flow, get_run_logger, tags, task
from prefect.cache_policies import NO_CACHE

BASE_URL = "https://dev.to/api"
CONCURRENCY = 10


# ## Implementing concurrent tasks
#
# First, we define a reusable task for fetching data from any URL. Note:
#
# * The `async` keyword makes this task asynchronous
# * We use a semaphore to limit concurrent requests
# * This task handles retries with exponential backoff


@task(retries=3, retry_delay_seconds=[10, 30, 60], cache_policy=NO_CACHE)
async def fetch_url(
    client: httpx.AsyncClient,
    semaphore: asyncio.BoundedSemaphore,
    url: str,
    params: dict | None = None,
) -> dict:
    """Generic task for fetching a URL"""
    async with semaphore:
        get_run_logger().info(f"Fetching {url}")
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


# Now we create a task that fetches multiple pages of article listings.
# It does this by:
#
# 1. Creating a list of fetch tasks (one per page)
# 2. Using `asyncio.gather()` to run them all concurrently
# 3. Extracting article IDs from the results


@task(cache_policy=NO_CACHE)
async def list_articles(
    client: httpx.AsyncClient,
    semaphore: asyncio.BoundedSemaphore,
    pages: int,
    per_page: int = 10,
) -> list[str]:
    """List (pages * per_page) article URLs from the Dev.to API"""
    _tasks = [
        fetch_url(
            client,
            semaphore,
            f"{BASE_URL}/articles",
            {"page": page, "per_page": per_page},
        )
        for page in range(1, pages + 1)
    ]
    _pages = await asyncio.gather(*_tasks)

    return [f"{BASE_URL}/articles/{_item['id']}" for _page in _pages for _item in _page]


# ## The orchestration flow
#
# Our flow coordinates the entire process:
#
# 1. Sets up a concurrency limit with a semaphore
# 2. Creates an async HTTP client
# 3. Gets all article URLs concurrently
# 4. Fetches full article details concurrently
#
# Notice how we're managing two levels of concurrency: page fetching and
# article fetching.


@flow
async def extract(pages: int) -> None:
    """Extract articles from the Dev.to API"""
    semaphore = asyncio.BoundedSemaphore(CONCURRENCY)

    async with httpx.AsyncClient() as client:
        article_urls = await list_articles(client, semaphore, pages)

        articles = [
            fetch_url(client, semaphore, article_url) for article_url in article_urls
        ]

        await asyncio.gather(*articles)


# ## Comparing with ThreadPoolTaskRunner
#
# The async approach shown above works well for I/O-bound tasks.
# Alternatively, you could use Prefect's ThreadPoolTaskRunner:
#
# ```python
# from prefect.task_runners import ThreadPoolTaskRunner
#
# @flow(task_runner=ThreadPoolTaskRunner(max_workers=10))
# def extract_with_threads(pages: int) -> None:
#     # Regular synchronous code here
#     # Tasks will automatically execute in thread pool
#     ...
# ```
#
# **When to use which approach:**
#
# * **Async/await**: When working with async libraries or needing fine-grained control
# * **ThreadPoolTaskRunner**: For simpler cases or when using synchronous libraries
# * **DaskTaskRunner**: For distributed computing across machines

if __name__ == "__main__":
    with tags("local"):
        asyncio.run(extract(pages=10))

# ### What just happened?
#
# When you ran this script:
#
# 1. Prefect registered the async tasks and flow
# 2. The flow created a semaphore limiting concurrency to 10 simultaneous requests
# 3. It fetched multiple pages of article listings concurrently (up to 10 at once)
# 4. It then fetched detailed data for ~100 articles concurrently (10 at a time)
# 5. All this happened while using just a single thread, thanks to async I/O
#
# ### Why This Is Important
#
# Concurrency is crucial for data pipelines that interact with external systems.
# With Prefect's support for async:
#
# * **Speed**: Workflows complete much faster by doing work in parallel
# * **Efficiency**: Resources are used optimally with controlled concurrency
# * **Resilience**: Each concurrent task can retry independently
# * **Responsiveness**: The workflow remains responsive even during heavy I/O
#
# The best part: you get these benefits while writing clean, maintainable code
# that looks almost identical to synchronous code, just with a few extra keywords.
