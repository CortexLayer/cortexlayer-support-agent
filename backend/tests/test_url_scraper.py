"""Tests for URL scraping utilities (sync + async)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.ingestion.url_scraper import (
    URLFetchError,
    scrape_url,
    scrape_url_sync,
)


# --------------------------------------------------------------------------
# SYNC TESTS
# --------------------------------------------------------------------------
@patch("backend.app.ingestion.url_scraper.requests.get")
def test_scrape_url_sync_success(mock_get):
    """Ensure synchronous scraper returns clean text + metadata."""
    mock_response = MagicMock()
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_get.return_value = mock_response

    text, meta = scrape_url_sync("https://example.com")

    assert "Hello world" in text
    assert meta["url"] == "https://example.com"


@patch("backend.app.ingestion.url_scraper.requests.get")
def test_scrape_url_sync_failure(mock_get):
    """Ensure synchronous scraper raises URLFetchError when request fails."""
    mock_get.side_effect = Exception("network error")

    with pytest.raises(URLFetchError):
        scrape_url_sync("https://badurl.com")


# --------------------------------------------------------------------------
# ASYNC TESTS
# --------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("backend.app.ingestion.url_scraper.httpx.AsyncClient")
async def test_scrape_url_async_success(mock_client):
    """Ensure async scraper extracts text correctly."""
    mock_response = MagicMock()
    mock_response.text = "<html><p>Async Hello</p></html>"

    mock_instance = AsyncMock()
    mock_instance.get.return_value = mock_response

    mock_client.return_value.__aenter__.return_value = mock_instance

    text, meta = await scrape_url("https://site.com")

    assert "Async Hello" in text
    assert meta["url"] == "https://site.com"


@pytest.mark.asyncio
@patch("backend.app.ingestion.url_scraper.httpx.AsyncClient")
async def test_scrape_url_async_failure(mock_client):
    """Ensure async scraper raises URLFetchError when network fails."""
    mock_instance = AsyncMock()
    mock_instance.get.side_effect = Exception("async network error")

    mock_client.return_value.__aenter__.return_value = mock_instance

    with pytest.raises(URLFetchError):
        await scrape_url("https://xyz.com")
