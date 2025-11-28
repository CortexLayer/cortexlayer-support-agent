"""Tests for file utilities."""

from backend.app.utils.file_utils import (
    get_file_extension,
    sanitize_filename,
    validate_file_size,
)


def test_validate_file_size():
    """Test that file size validation works correctly."""
    assert validate_file_size(1024 * 1024 * 2, 5) is True  # 2MB <= 5MB
    assert validate_file_size(1024 * 1024 * 6, 5) is False  # 6MB > 5MB


def test_get_file_extension():
    """Test extracting file extensions from filenames."""
    assert get_file_extension("document.pdf") == ".pdf"
    assert get_file_extension("photo.JPG").lower() == ".jpg"


def test_sanitize_filename():
    """Test sanitizing filenames by removing unsafe characters."""
    assert sanitize_filename("hello world!.pdf") == "hello_world_.pdf"
    assert len(sanitize_filename("a" * 300 + ".txt")) <= 255
