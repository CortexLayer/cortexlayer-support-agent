"""URL Scraper module providing async and sync scraping utilities."""

from typing import Dict, Tuple

import httpx
import requests
import trafilatura

from backend.app.utils.logger import logger


# Custom Exceptions
class URLFetchError(Exception):
    """Raised when fetching the URL fails."""


class URLExtractionError(Exception):
    """Raised when trafilatura fails to extract content."""


# SYNC SCRAPER
def scrape_url_sync(url: str, timeout: int = 30) -> Tuple[str, Dict]:
    """Synchronous URL scraping using requests.

    Returns:
        (text, metadata) tuple.

    Raises:
        URLFetchError, URLExtractionError
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except Exception as exc:
        logger.error(f"Sync fetch failed: {exc}")
        raise URLFetchError(f"Failed to fetch URL: {url}") from exc

    text = trafilatura.extract(html, include_comments=False, include_tables=True)

    if not text:
        raise URLExtractionError("No extractable text found")

    metadata = {"url": url}
    return text.strip(), metadata


# ASYNC SCRAPER
async def scrape_url(url: str, timeout: int = 30) -> Tuple[str, Dict]:
    """Asynchronous URL scraping using httpx.AsyncClient.

    Returns:
        (text, metadata)

    Raises:
        URLFetchError, URLExtractionError
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout, follow_redirects=True)
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        logger.error(f"Async fetch failed: {exc}")
        raise URLFetchError(f"Failed to fetch URL: {url}") from exc

    text = trafilatura.extract(html, include_comments=False, include_tables=True)

    if not text:
        raise URLExtractionError("No extractable text found")

    metadata = {"url": url}
    return text.strip(), metadata
