import logging

from storage3.exceptions import StorageApiError
from storage3.types import UploadResponse
from supabase import AsyncClient

from settings import ALLOWED_MIME_TYPES

logger = logging.getLogger(__name__)

async def get_or_create_bucket(
    db: AsyncClient,
    bucket_name: str = "CV",
    file_types: list[str] | None = None,
    max_size: int = 2 * 1024 * 1024,
):
    """Retrieves the details of an existing Storage bucket
    if the bucket doesn't exist, it creates it.
    """
    try:
        return await db.storage.get_bucket(bucket_name)

    except StorageApiError as e:
        if "Bucket not found" in str(e) or e.status_code == 404:
            if file_types is None:
                file_types = ALLOWED_MIME_TYPES
            return await db.storage.create_bucket(
                id=bucket_name,
                options={
                    "public": False,
                    "allowed_mime_types": file_types,
                    "file_size_limit": max_size,
                },
            )
        raise e

async def upload_file(
    db: AsyncClient,
    file_bytes: bytes,
    destination_path: str,
    bucket: str = "CV"
) -> UploadResponse:
    """
    Asynchronously loads the bytes of a file into Supabase Storage.
    """
    await get_or_create_bucket(db, bucket, file_types=ALLOWED_MIME_TYPES)

    response = await db.storage.from_(bucket).upload(
        file=file_bytes,
        path=destination_path,
        file_options={
            "cache-control": "3600",
            "upsert": "true"
        }
    )
    return response

async def remove_file(db: AsyncClient, full_path: str) -> None:
    """Deletes a single file from Supabase Storage by full path."""
    try:
        bucket_name, storage_path = full_path.split("/", maxsplit=1)
        await db.storage.from_(bucket_name).remove([storage_path])
        logger.info("Файл %s успішно видалено зі Storage", full_path)
    except Exception as e:
        logger.error("Помилка видалення файлу %s зі Storage: %s", full_path, e, exc_info=True)