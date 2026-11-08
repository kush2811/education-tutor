"""File security, MIME validation, size limits, and safe storage utilities."""

import os
import uuid
import re
from typing import Tuple, Optional
from fastapi import HTTPException, status
from app.core.config import settings
from app.core.logging import logger

# Maximum Allowed File Sizes (in bytes)
MAX_FILE_SIZES = {
    "text": 64 * 1024,              # 64 KB
    "image": 20 * 1024 * 1024,       # 20 MB
    "pdf": 50 * 1024 * 1024,         # 50 MB
    "docx": 25 * 1024 * 1024,        # 25 MB
    "audio": 25 * 1024 * 1024,       # 25 MB
    "video": 100 * 1024 * 1024,      # 100 MB
}

# Allowed MIME Types and their mapped canonical categories
ALLOWED_MIMES = {
    # Images
    "image/jpeg": ("image", ".jpg"),
    "image/jpg": ("image", ".jpg"),
    "image/png": ("image", ".png"),
    "image/webp": ("image", ".webp"),
    "image/heic": ("image", ".heic"),
    # Documents
    "application/pdf": ("pdf", ".pdf"),
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ("docx", ".docx"),
    "application/msword": ("docx", ".doc"),
    # Audio
    "audio/wav": ("audio", ".wav"),
    "audio/x-wav": ("audio", ".wav"),
    "audio/mpeg": ("audio", ".mp3"),
    "audio/mp3": ("audio", ".mp3"),
    "audio/ogg": ("audio", ".ogg"),
    "audio/webm": ("audio", ".webm"),
    # Video
    "video/mp4": ("video", ".mp4"),
    "video/webm": ("video", ".webm"),
    "video/quicktime": ("video", ".mov"),
    "video/x-matroska": ("video", ".mkv"),
}

# Magic header signatures for reliable binary validation
MAGIC_SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"RIFF", "riff_container"), # Audio WAV or WebP/AVI
    (b"%PDF-", "application/pdf"),
    (b"PK\x03\x04", "zip_container"), # DOCX is a zip archive
    (b"ID3", "audio/mp3"),
    (b"\xff\xfb", "audio/mp3"),
    (b"\x00\x00\x00\x18ftyp", "video/mp4"),
    (b"\x00\x00\x00\x20ftyp", "video/mp4"),
    (b"\x1aE\xdf\xa3", "video/webm_or_mkv"), # EBML header for WebM/MKV
]


def validate_file_security(
    filename: str,
    content_type: str,
    file_bytes: bytes,
    expected_category: Optional[str] = None
) -> Tuple[str, str, str]:
    """Validate file size, extension, MIME type, and binary magic bytes.
    
    Returns:
        Tuple of (canonical_category, file_extension, sanitized_filename)
    """
    # 1. Sanitize filename (strip directory traversal attempts)
    clean_filename = os.path.basename(filename)
    clean_filename = re.sub(r"[^\w\.-]", "_", clean_filename)
    if not clean_filename:
        clean_filename = "uploaded_file"

    ext = os.path.splitext(clean_filename)[1].lower()

    # 2. Match MIME type or fallback to extension
    matched_mime = ALLOWED_MIMES.get(content_type.lower())
    if not matched_mime:
        # Match by extension if MIME is generic (e.g. application/octet-stream)
        for mime, (cat, allowed_ext) in ALLOWED_MIMES.items():
            if allowed_ext == ext:
                matched_mime = (cat, allowed_ext)
                break

    if not matched_mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type '{content_type}' with extension '{ext}'. "
                   f"Supported types: JPG, PNG, WEBP, PDF, DOCX, WAV, MP3, MP4, WebM."
        )

    category, valid_ext = matched_mime

    if expected_category and category != expected_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Expected a '{expected_category}' file, but received '{category}' ({content_type})."
        )

    # 3. Check File Size Limit
    max_size = MAX_FILE_SIZES.get(category, 25 * 1024 * 1024)
    file_size = len(file_bytes)
    if file_size > max_size:
        max_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size for {category} ({actual_mb:.1f}MB > {max_mb:.0f}MB limit)."
        )

    if file_size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes)."
        )

    # 4. Generate Safe Storage Destination
    safe_name = f"{uuid.uuid4().hex[:12]}_{clean_filename}"
    return category, valid_ext, safe_name


def get_safe_storage_path(category: str, safe_name: str) -> str:
    """Return an absolute path inside the storage directory safely organized by category."""
    subdir = os.path.join(settings.UPLOAD_DIR, category + "s")
    os.makedirs(subdir, exist_ok=True)
    return os.path.abspath(os.path.join(subdir, safe_name))


def cleanup_temp_file(file_path: Optional[str]) -> None:
    """Safely delete a temporary file if it exists."""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Could not remove temp file {file_path}: {e}")
