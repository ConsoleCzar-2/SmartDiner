import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from google.cloud import storage
import logging
from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

def get_file_extension(filename: str) -> str:
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""

async def upload_image_to_gcs(
    file: UploadFile,
    entity_type: str,
    entity_id: str
) -> str:
    """
    Validates and uploads an image file to the GCS image bucket.
    Returns the public URL of the uploaded image.
    """
    if not settings.gcs_image_bucket_name:
        raise HTTPException(status_code=500, detail="GCS image bucket not configured")

    ext = get_file_extension(file.filename or "")
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read the file contents to check size and to upload
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large (max 5 MB)")

    # Reset file pointer if needed, though we will upload `contents` directly
    await file.seek(0)

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.{ext}"
    blob_name = f"images/{entity_type}/{entity_id}/{unique_filename}"

    try:
        # Run synchronous GCS upload in executor to avoid blocking
        import asyncio
        loop = asyncio.get_running_loop()

        def _sync_upload():
            client = storage.Client(project=settings.gcp_project_id if settings.gcp_project_id else None)
            bucket = client.bucket(settings.gcs_image_bucket_name)
            blob = bucket.blob(blob_name)
            
            # Use appropriate content type
            content_type = file.content_type
            if not content_type:
                content_type = f"image/{ext}" if ext != "jpg" else "image/jpeg"
                
            blob.upload_from_string(
                contents,
                content_type=content_type
            )
            
            # Make the blob publicly readable (if bucket uniform access isn't strictly overriding)
            # Actually, if uniform-bucket-level-access is true and bucket is public, this isn't needed.
            # But we can try to return the standard googleapis link.
            return f"https://storage.googleapis.com/{settings.gcs_image_bucket_name}/{blob_name}"

        public_url = await loop.run_in_executor(None, _sync_upload)
        return public_url

    except Exception as e:
        logger.error(f"Failed to upload image to GCS: {e}")
        raise HTTPException(status_code=500, detail="Failed to upload image")
