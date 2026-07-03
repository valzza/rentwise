import os
import uuid
from typing import Optional
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.repositories.file_repository import FileRepository
from app.models.audit_models import File

ALLOWED_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


class FileService:
    def __init__(self, repo: FileRepository):
        self.repo = repo

    async def upload(
        self,
        upload: UploadFile,
        entity: str,
        entity_id: int,
        uploaded_by: int,
        link_property: bool = False,
    ) -> File:
        # ── Validate MIME type ──────────────────────────────────────────
        ext = ALLOWED_CONTENT_TYPES.get(upload.content_type)
        if ext is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {upload.content_type}. Allowed: JPG, PNG, WEBP, GIF.",
            )

        # ── Read + validate size ────────────────────────────────────────
        contents = await upload.read()
        max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(contents) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds the {settings.MAX_FILE_SIZE_MB} MB limit.",
            )

        # ── Sanitize: never trust the client filename for the path ──────
        safe_name = f"{uuid.uuid4().hex}{ext}"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        disk_path = os.path.join(settings.UPLOAD_DIR, safe_name)
        with open(disk_path, "wb") as fh:
            fh.write(contents)

        # file_path stores the public-relative name served from /uploads
        record = await self.repo.create(
            entity=entity,
            entity_id=entity_id,
            filename=os.path.basename(upload.filename or safe_name),
            file_path=safe_name,
            file_size=len(contents),
            uploaded_by=uploaded_by,
            created_by=uploaded_by,
            updated_by=uploaded_by,
        )

        if link_property and entity == "property":
            is_primary = not await self.repo.property_has_images(entity_id)
            await self.repo.link_property_image(entity_id, record.id, is_primary, uploaded_by)

        return record
