"""Pydantic schemas for uploaded files and media assets."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AssetResponse(BaseModel):
    """Schema for returning uploaded file details."""
    id: str
    file_name: str
    file_type: str
    file_path: str
    file_size: int
    mime_type: str
    extracted_metadata: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """Schema for upload acknowledgement."""
    asset_id: str
    file_name: str
    file_type: str
    file_size: int
    status: str
    message: str

