"""Endpoints for file uploads and asset management."""

import os
import uuid
import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.db.session import get_db
from app.models.asset import UploadedAsset
from app.schemas.asset import FileUploadResponse, AssetResponse

router = APIRouter()

ALLOWED_MIME_TYPES = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "image/heic": "image",
    "application/pdf": "document",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "document",
    "audio/wav": "audio",
    "audio/mpeg": "audio",
    "audio/webm": "audio",
    "audio/ogg": "audio",
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image, document, or audio file"
)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """Store an uploaded asset locally and record metadata in database."""
    content_type = file.content_type or "application/octet-stream"
    
    # MIME type detection
    file_type = ALLOWED_MIME_TYPES.get(content_type)
    if not file_type:
        # Fallback check based on extension
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            file_type = "image"
        elif ext in [".pdf", ".docx"]:
            file_type = "document"
        elif ext in [".wav", ".mp3", ".ogg", ".webm"]:
            file_type = "audio"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{content_type}'. Allowed types: JPG, PNG, WEBP, PDF, DOCX, WAV, MP3."
            )

    asset_id = str(uuid.uuid4())
    safe_filename = f"{asset_id}_{file.filename}"
    upload_subdir = os.path.join(settings.UPLOAD_DIR, file_type + "s")
    os.makedirs(upload_subdir, exist_ok=True)
    destination_path = os.path.join(upload_subdir, safe_filename)

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds maximum allowed limit (50MB)."
        )

    # Save to disk
    async with aiofiles.open(destination_path, "wb") as f:
        await f.write(contents)

    # Record in database
    new_asset = UploadedAsset(
        id=asset_id,
        session_id=session_id,
        file_name=file.filename or "uploaded_file",
        file_type=file_type,
        file_path=destination_path,
        file_size=len(contents),
        mime_type=content_type,
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

    logger.info(f"Uploaded file {file.filename} saved to {destination_path} (asset_id={asset_id})")

    return FileUploadResponse(
        asset_id=new_asset.id,
        file_name=new_asset.file_name,
        file_type=new_asset.file_type,
        file_size=new_asset.file_size,
        status="uploaded",
        message="File successfully saved and cataloged."
    )


@router.get(
    "/assets/{asset_id}",
    response_model=AssetResponse,
    summary="Get uploaded file metadata"
)
def get_asset(asset_id: str, db: Session = Depends(get_db)) -> AssetResponse:
    """Retrieve metadata for a recorded asset."""
    asset = db.query(UploadedAsset).filter(UploadedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found."
        )
    return asset
