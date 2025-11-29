"""Tests for URL scraper (sync + async)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.ingestion.url_scraper import (
    URLFetchError,
    scrape_url,
    scrape_url_sync,
)


# SYNC SUCCESS
@patch("backend.app.ingestion.url_scraper.requests.get")
def test_scrape_url_sync_success(mock_get):
    """Test successful sync scraping."""
    mock_response = MagicMock()
    mock_response.text = "<html><body><p>Hello world</p></body></html>"
    mock_response.raise_for_status.return_value = None

    mock_get.return_value = mock_response

    text, meta = scrape_url_sync("https://example.com")

    assert "Hello world" in text
    assert meta["url"] == "https://example.com"


# SYNC FAILURE
@patch("backend.app.ingestion.url_scraper.requests.get")
def test_scrape_url_sync_failure(mock_get):
    """Test sync fetch failure raises URLFetchError."""
    mock_get.side_effect = Exception("network error")

    with pytest.raises(URLFetchError):
        scrape_url_sync("https://badurl.com")


# ASYNC SUCCESS
@pytest.mark.asyncio
@patch("backend.app.ingestion.url_scraper.httpx.AsyncClient")
async def test_scrape_url_async_success(mock_client):
    """Test successful async scraping."""
    mock_resp = MagicMock()
    mock_resp.text = "<html><p>Async Hello</p></html>"
    mock_resp.raise_for_status.return_value = None

    mock_instance = AsyncMock()
    mock_instance.get.return_value = mock_resp

    mock_client.return_value.__aenter__.return_value = mock_instance

    text, meta = await scrape_url("https://async.com")

    assert "Async Hello" in text
    assert meta["url"] == "https://async.com"


# ASYNC FAILURE
@pytest.mark.asyncio
@patch("backend.app.ingestion.url_scraper.httpx.AsyncClient")
async def test_scrape_url_async_failure(mock_client):
    """Test async fetch failure raises URLFetchError."""
    mock_instance = AsyncMock()
    mock_instance.get.side_effect = Exception("async error")

    mock_client.return_value.__aenter__.return_value = mock_instance

    with pytest.raises(URLFetchError):
        await scrape_url("https://fail.com")
