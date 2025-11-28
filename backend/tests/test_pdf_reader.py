"""Tests for PDF text extraction utility."""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.ingestion.pdf_reader import extract_pdf_text


def test_extract_pdf_text_pypdf2_success():
    """Test extraction when PyPDF2 works correctly."""
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Hello from PDF!"

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page]

    with patch("backend.app.ingestion.pdf_reader.PdfReader", return_value=mock_reader):
        result = extract_pdf_text(b"%PDF dummy bytes")

    assert result == "Hello from PDF!"


def test_extract_pdf_text_pdfminer_fallback():
    """Test fallback to pdfminer when PyPDF2 returns insufficient text."""
    mock_reader = MagicMock()
    mock_reader.pages = [MagicMock(extract_text=lambda: "")]

    with patch("backend.app.ingestion.pdf_reader.PdfReader", return_value=mock_reader):
        with patch(
            "backend.app.ingestion.pdf_reader.pdfminer_extract",
            return_value="PDFMiner extracted text",
        ):
            result = extract_pdf_text(b"%PDF fake")

    assert result == "PDFMiner extracted text"


def test_extract_pdf_text_failure():
    """Test extraction failure when both PyPDF2 and pdfminer fail."""
    with patch(
        "backend.app.ingestion.pdf_reader.PdfReader",
        side_effect=Exception("PyPDF2 broken"),
    ):
        with patch(
            "backend.app.ingestion.pdf_reader.pdfminer_extract",
            side_effect=Exception("pdfminer broken"),
        ):
            err = pytest.raises(Exception, extract_pdf_text, b"fake pdf")

    assert "Failed to extract text from PDF" in str(err.value)
