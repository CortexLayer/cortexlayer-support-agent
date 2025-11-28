"""Tests for S3 utility functions."""

from unittest.mock import MagicMock, patch

from backend.app.utils.s3 import delete_file, download_file, upload_file


@patch("backend.app.utils.s3.s3_client")
def test_upload_file(mock_s3):
    """Test uploading a file to S3."""
    mock_s3.put_object.return_value = {}

    result = upload_file(b"hello", "test/key.txt")

    assert result is True
    mock_s3.put_object.assert_called_once()


@patch("backend.app.utils.s3.s3_client")
def test_download_file(mock_s3):
    """Test downloading a file from S3."""
    mock_body = MagicMock()
    mock_body.read.return_value = b"hello world"

    mock_s3.get_object.return_value = {"Body": mock_body}

    result = download_file("test/key.txt")

    assert result == b"hello world"
    mock_s3.get_object.assert_called_once()


@patch("backend.app.utils.s3.s3_client")
def test_delete_file(mock_s3):
    """Test deleting a file from S3."""
    mock_s3.delete_object.return_value = {}

    result = delete_file("test/key.txt")

    assert result is True
    mock_s3.delete_object.assert_called_once()
