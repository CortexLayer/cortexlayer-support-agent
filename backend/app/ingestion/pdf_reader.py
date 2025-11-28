"""PDF text extraction utility with PyPDF2 first and pdfminer fallback."""

from io import BytesIO

from pdfminer.high_level import extract_text as pdfminer_extract
from PyPDF2 import PdfReader

from backend.app.utils.logger import logger


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF with fallback.

    First attempt extraction using PyPDF2 (fast). If PyPDF2 fails or returns
    insufficient text, fallback to pdfminer (more reliable).
    """
    # Try PyPDF2 first
    try:
        pdf_file = BytesIO(pdf_bytes)
        reader = PdfReader(pdf_file)

        text = ""
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text += page_text + "\n"

        # If PyPDF2 produced ANY text, return it
        if text.strip():
            logger.info("PDF extracted using PyPDF2.")
            return text.strip()

        logger.warning("PyPDF2 returned empty text, trying pdfminer.")

    except Exception as err:  # noqa: BLE001
        logger.warning(f"PyPDF2 failed: {err}")

    # Fallback to pdfminer
    try:
        pdf_file = BytesIO(pdf_bytes)
        text = pdfminer_extract(pdf_file)
        logger.info("PDF extracted using pdfminer.")
        return text.strip()
    except Exception as err:  # noqa: BLE001
        logger.error(f"PDF extraction failed entirely: {err}")
        raise Exception("Failed to extract text from PDF") from err
