"""URL scraper module providing async and sync web scraping utilities."""

from typing import Dict, Tuple

import httpx
import requests
import trafilatura

from backend.app.utils.logger import logger


def scrape_url_sync(url: str, timeout: int = 30) -> Tuple[str, Dict]:
    """Scrape a URL synchronously using `requests`.

    Args:
        url: URL to fetch.
        timeout: Timeout duration.

    Returns:
        A tuple containing:
            - extracted text (str)
            - metadata (dict)

    Raises:
        Exception: If fetching or extraction fails.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except Exception as err:  # noqa: BLE001
        raise Exception(f"Failed to fetch URL: {err}") from err

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if not text:
        raise Exception("No content extracted from URL")

    metadata = {"url": url}

    logger.info("Sync scraping completed successfully.")
    return text.strip(), metadata


async def scrape_url(url: str, timeout: int = 30) -> Tuple[str, Dict]:
    """Scrape a URL asynchronously using httpx.

    Args:
        url: URL to fetch.
        timeout: Timeout duration.

    Returns:
        A tuple containing:
            - extracted text (str)
            - metadata (dict)

    Raises:
        Exception: If fetching or extraction fails.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                timeout=timeout,
                follow_redirects=True,
            )
            response.raise_for_status()
            html = response.text
    except Exception as err:  # noqa: BLE001
        raise Exception(f"Failed to fetch URL: {err}") from err

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    )

    if not text:
        raise Exception("No content extracted from URL")

    metadata = {"url": url}

    logger.info("Async scraping completed successfully.")
    return text.strip(), metadata
