# ---
# title: Simple web scraper
# description: Learn how to scrape article content from web pages with Prefect tasks, retries, and automatic logging.
# icon: globe
# dependencies: ["prefect", "requests", "beautifulsoup4"]
# cmd: ["python", "01_getting_started/02_simple_web_scraper.py"]
# tags: [getting_started, webscraping, tasks, retries]
# draft: false
# ---
#
# This example shows how Prefect enhances regular Python code without getting in its way.
# You'll write code exactly as you normally would, and Prefect's decorators add production-ready
# features with zero boilerplate.
#
# In this example you will:
# 1. Write regular Python functions for web scraping
# 2. Add production features ([retries](https://docs.prefect.io/v3/develop/write-tasks#retries), [logging](https://docs.prefect.io/v3/develop/logging#configure-logging)) with just two decorators:
#    - `@task` - Turn any function into a [retryable, observable unit](https://docs.prefect.io/v3/develop/write-tasks#write-and-run-tasks)
#    - `@flow` - Compose tasks into a [reliable pipeline](https://docs.prefect.io/v3/develop/write-flows#write-and-run-flows)
# 3. Keep your code clean and Pythonic - no framework-specific patterns needed
#
# ## The Power of Regular Python
# Notice how the code below is just standard Python with two decorators. You could remove
# the decorators and the code would still work - Prefect just makes it more resilient.
#
# - Regular Python functions? ✓
# - Standard libraries (requests, BeautifulSoup)? ✓
# - Normal control flow (if/else, loops)? ✓
# - Prefect's magic? Just two decorators! ✓

from __future__ import annotations

import requests
from bs4 import BeautifulSoup
from prefect import flow, task

# ## Defining tasks
#
# We separate network IO from parsing so both pieces can be retried or cached independently.


@task(retries=3, retry_delay_seconds=2)
def fetch_html(url: str) -> str:
    """Download page HTML (with retries).

    This is just a regular requests call - Prefect adds retry logic
    without changing how we write the code."""
    print(f"Fetching {url} …")
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.text


@task
def parse_article(html: str) -> str:
    """Extract article text, skipping code blocks.

    Regular BeautifulSoup parsing with standard Python string operations.
    Prefect adds observability without changing the logic."""
    soup = BeautifulSoup(html, "html.parser")

    # Find main content - just regular BeautifulSoup
    article = soup.find("article") or soup.find("main")
    if not article:
        return ""

    # Standard Python all the way
    for code in article.find_all(["pre", "code"]):
        code.decompose()

    content = []
    for elem in article.find_all(["h1", "h2", "h3", "p", "ul", "ol", "li"]):
        text = elem.get_text().strip()
        if not text:
            continue

        if elem.name.startswith("h"):
            content.extend(["\n" + "=" * 80, text.upper(), "=" * 80 + "\n"])
        else:
            content.extend([text, ""])

    return "\n".join(content)


# ## Defining a flow
#
# `@flow` elevates a function to a *flow* – the orchestration nucleus that can call
# tasks, other flows, and any Python you need. We enable `log_prints=True` so each
# `print()` surfaces in Prefect Cloud or the local API.


@flow(log_prints=True)
def scrape(urls: list[str] | None = None) -> None:
    """Scrape and print article content from URLs.

    A regular Python function that composes our tasks together.
    Prefect adds logging and dependency management automatically."""

    if urls:
        for url in urls:
            content = parse_article(fetch_html(url))
            print(content if content else "No article content found.")


# ## Run it!
#
# Feel free to tweak the URL list or the regex and re-run. Prefect hot-reloads your
# code instantly – no container builds required.

if __name__ == "__main__":
    urls = [
        "https://www.prefect.io/blog/airflow-to-prefect-why-modern-teams-choose-prefect"
    ]
    scrape(urls=urls)

# ## What just happened?
#
# When you ran this script, Prefect did a few things behind the scenes:
# 1. Turned each decorated function into a *task run* or *flow run* with structured state.
# 2. Applied retry logic to the network call – a flaky connection would auto-retry up to 3 times.
# 3. Captured all `print()` statements so you can view them in the Prefect UI or logs.
# 4. Passed the HTML between tasks **in memory** – no external storage required.
#
# Yet the code itself is standard Python. You could copy-paste the body of `fetch_html` or
# `parse_article` into a notebook and they'd work exactly the same.
#
# ## Key Takeaways
#
# * **Less boilerplate, more Python** – You focus on the scraping logic, Prefect adds production features.
# * **Observability out of the box** – Every run is tracked, making debugging and monitoring trivial.
# * **Portability** – The same script runs on your laptop today and on Kubernetes tomorrow.
# * **Reliability** – Retries, timeouts, and state management are just one decorator away.
#
# Happy scraping – and happy orchestrating! 🎉
