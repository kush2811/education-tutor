"""Endpoints for multimodal input ingestion: text, images, PDF, DOCX, audio, and video."""

import os
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import UploadedAsset
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user_optional
from app.core.logging import logger
from app.core.file_security import (
    validate_file_security,
    get_safe_storage_path,
    cleanup_temp_file,
)
from app.schemas.unified_input import (
    UnifiedQuestionPayload,
    TextProcessRequest,
    AudioTranscriptionResponse,
)
from app.schemas.asset import FileUploadResponse, AssetResponse
from app.services.unified_pipeline import unified_input_pipeline

router = APIRouter()


@router.post(
    "/text",
    response_model=UnifiedQuestionPayload,
    summary="Process and normalize student text or mathematical inquiry"
)
def process_text_input(payload: TextProcessRequest) -> UnifiedQuestionPayload:
    """Normalize whitespace, convert bracket LaTeX delimiters to standard $ and $$,
    extract math formulas, and identify the subject domain."""
    return unified_input_pipeline.process(
        input_type="text",
        data=payload.text
    )


@router.post(
    "/image",
    response_model=UnifiedQuestionPayload,
    status_code=status.HTTP_200_OK,
    summary="Ingest image, preprocess contrast/deskew, and execute vision OCR"
)
async def process_image_input(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Ingest textbook photo or student handwritten math note."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "upload.jpg",
        content_type=file.content_type or "image/jpeg",
        file_bytes=file_bytes,
        expected_category="image"
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    # Record in database
    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type="image",
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "image/jpeg"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    # Process via multimodal vision pipeline
    result = unified_input_pipeline.process(
        input_type="image",
        data=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/pdf",
    response_model=UnifiedQuestionPayload,
    summary="Ingest PDF worksheet or textbook chapter with page references and tables"
)
async def process_pdf_input(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Extract page-by-page text, tables, and academic citation anchors from PDF."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "worksheet.pdf",
        content_type=file.content_type or "application/pdf",
        file_bytes=file_bytes,
        expected_category="pdf"
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type="document",
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type="application/pdf"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    result = unified_input_pipeline.process(
        input_type="pdf",
        data=file_bytes,
        filename=file.filename,
        mime_type="application/pdf",
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/docx",
    response_model=UnifiedQuestionPayload,
    summary="Ingest Word document with paragraphs, headings, and table structures"
)
async def process_docx_input(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Extract structured document sections, headings, and tables from DOCX."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "worksheet.docx",
        content_type=file.content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_bytes=file_bytes,
        expected_category="docx"
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type="document",
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/docx"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    result = unified_input_pipeline.process(
        input_type="docx",
        data=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/audio",
    response_model=UnifiedQuestionPayload,
    summary="Process student recorded audio question and execute Speech-to-Text"
)
async def process_audio_input(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Transcribe spoken question and return structured representation for confirmation."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "question.wav",
        content_type=file.content_type or "audio/wav",
        file_bytes=file_bytes,
        expected_category="audio"
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type="audio",
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "audio/wav"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    result = unified_input_pipeline.process(
        input_type="audio",
        data=file_bytes,
        filename=file.filename,
        mime_type=file.content_type or "audio/wav",
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/video",
    response_model=UnifiedQuestionPayload,
    summary="Process educational video clip with keyframe sampling and transcript fusion"
)
async def process_video_input(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Ingest lecture clip, extract audio transcript, sample keyframes, and combine context."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "lecture.mp4",
        content_type=file.content_type or "video/mp4",
        file_bytes=file_bytes,
        expected_category="video"
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type="video",
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "video/mp4"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    result = unified_input_pipeline.process(
        input_type="video",
        data=file_bytes,
        filename=file.filename,
        mime_type=file.content_type or "video/mp4",
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/unified",
    response_model=UnifiedQuestionPayload,
    summary="Master unified endpoint: auto-detects file category or text and processes"
)
async def process_unified_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
) -> UnifiedQuestionPayload:
    """Accepts any valid multimodal file (image, PDF, DOCX, audio, video), validates security,
    saves safely, routes to specialized processor, and returns the common UnifiedQuestionPayload."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "input_file",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    asset = UploadedAsset(
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type=category,
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/octet-stream"
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    result = unified_input_pipeline.process(
        input_type=category,
        data=file_bytes,
        filename=file.filename,
        mime_type=file.content_type,
        file_path=dest_path
    )
    if result.source_file:
        result.source_file.asset_id = asset.id

    return result


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Standard asset upload endpoint (Phase 1 compatibility)"
)
async def upload_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> FileUploadResponse:
    """Store an uploaded asset locally and record metadata in database with user ownership."""
    file_bytes = await file.read()
    category, ext, safe_name = validate_file_security(
        filename=file.filename or "uploaded_file",
        content_type=file.content_type or "application/octet-stream",
        file_bytes=file_bytes
    )

    dest_path = get_safe_storage_path(category, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file_bytes)

    user_id = current_user.id if current_user else None

    new_asset = UploadedAsset(
        user_id=user_id,
        session_id=session_id,
        file_name=file.filename or safe_name,
        file_type=category,
        file_path=dest_path,
        file_size=len(file_bytes),
        mime_type=file.content_type or "application/octet-stream",
    )
    db.add(new_asset)
    db.commit()
    db.refresh(new_asset)

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
def get_asset(
    asset_id: str,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> AssetResponse:
    """Retrieve metadata for a recorded asset with privacy ownership check."""
    asset = db.query(UploadedAsset).filter(UploadedAsset.id == asset_id).first()
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found."
        )

    # Privacy Check: User cannot access another user's asset
    if asset.user_id:
        if not current_user or current_user.id != asset.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this private asset."
            )

    return asset
