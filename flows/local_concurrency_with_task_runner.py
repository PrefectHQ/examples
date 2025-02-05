"""Implements a data extract flow using task runner concurrency"""

from typing import Any

import httpx
from prefect import flow, get_run_logger, tags, task, unmapped
from prefect.futures import as_completed
from prefect.task_runners import ThreadPoolTaskRunner

BASE_URL = "https://dev.to/api"
CONCURRENCY = 10


@task(
    retries=3,
    retry_delay_seconds=[10, 30, 60],
)
def fetch_url(url: str, params: dict | None = None) -> dict[str, Any]:
    """Generic task for fetching a URL"""
    get_run_logger().info(f"Fetching {url}")
    response = httpx.get(url, params=params)
    response.raise_for_status()
    return response.json()


@task
def list_articles(pages: int, per_page: int = 10) -> list[str]:
    """List (pages * per_page) article URLs from the Dev.to API"""

    _pages = fetch_url.map(
        unmapped(f"{BASE_URL}/articles"),
        [{"page": page, "per_page": per_page} for page in range(1, pages + 1)],
    ).result()

    return [
        f"{BASE_URL}/articles/{article['id']}" for page in _pages for article in page
    ]


@flow(task_runner=ThreadPoolTaskRunner(max_workers=CONCURRENCY))
def extract(pages: int) -> None:
    """Extract articles from the Dev.to API"""
    article_urls = list_articles(pages)

    _articles = fetch_url.map(article_urls)

    # Log the title of each article as they become ready
    # alternatively, _articles.wait() will wait for all articles
    for _article in as_completed(_articles):
        get_run_logger().info(_article.result()["title"])


if __name__ == "__main__":
    with tags("local"):
        extract(pages=10)
