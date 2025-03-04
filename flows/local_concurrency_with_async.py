# /// script
# dependencies = ["prefect"]
# ///

"""Implement extract flow using Python native async concurrency"""

import asyncio

import httpx
from prefect import flow, get_run_logger, tags, task
from prefect.cache_policies import NO_CACHE

BASE_URL = "https://dev.to/api"
CONCURRENCY = 10


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


if __name__ == "__main__":
    with tags("local"):
        asyncio.run(extract(pages=10))
