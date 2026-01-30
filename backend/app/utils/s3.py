"""S3 utility functions for uploading, downloading, deleting files."""

import boto3
from botocore.exceptions import ClientError

from backend.app.core.config import settings
from backend.app.utils.logger import logger

_s3_client = None


def get_s3_client():
    """Lazy-initialize and return S3 client."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=settings.DO_SPACES_REGION,
            endpoint_url=f"https://{settings.DO_SPACES_REGION}.digitaloceanspaces.com",
            aws_access_key_id=settings.DO_SPACES_KEY,
            aws_secret_access_key=settings.DO_SPACES_SECRET,
        )
    return _s3_client


def upload_file(file_data: bytes, key: str) -> bool:
    """Upload a file to S3."""
    try:
        get_s3_client().put_object(
            Bucket=settings.DO_SPACES_BUCKET,
            Key=key,
            Body=file_data,
        )
        logger.info("Uploaded to S3: %s", key)
        return True
    except ClientError as exc:
        logger.error("S3 upload failed: %s", exc)
        return False


def download_file(key: str) -> bytes:
    """Download a file from S3."""
    try:
        response = get_s3_client().get_object(
            Bucket=settings.DO_SPACES_BUCKET,
            Key=key,
        )
        return response["Body"].read()
    except ClientError as exc:
        logger.error("S3 download failed: %s", exc)
        raise


def delete_file(key: str) -> bool:
    """Delete a file from S3."""
    try:
        get_s3_client().delete_object(
            Bucket=settings.DO_SPACES_BUCKET,
            Key=key,
        )
        logger.info("Deleted from S3: %s", key)
        return True
    except ClientError as exc:
        logger.error("S3 delete failed: %s", exc)
        return False


def list_bucket_safe() -> None:
    """Best-effort S3 connectivity check."""
    get_s3_client().list_objects_v2(
        Bucket=settings.DO_SPACES_BUCKET,
        MaxKeys=1,
    )
