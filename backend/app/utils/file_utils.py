"""File utility helpers for validating, sanitizing, and inspecting uploaded files."""

import os
import re


def validate_file_size(file_size: int, max_size_mb: int) -> bool:
    """Validate file size in bytes against a maximum size in MB.

    Args:
        file_size (int): Size of the file in bytes.
        max_size_mb (int): Maximum allowed size in MB.

    Returns:
        bool: True if file size is within limit, else False.
    """
    max_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_bytes


def get_file_extension(filename: str) -> str:
    """Extract and return lowercase file extension from filename.

    Args:
        filename (str): Original filename.

    Returns:
        str: File extension (e.g., ".pdf", ".txt")
    """
    return os.path.splitext(filename)[1].lower()


def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing unsafe characters and limiting length.

    Args:
        filename (str): Raw filename from user upload.

    Returns:
        str: Safe filename with only allowed characters.
    """
    safe_name = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    return safe_name[:255]
