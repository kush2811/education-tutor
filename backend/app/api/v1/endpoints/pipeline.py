"""Endpoints for Phase 10: Complete End-to-End Educational Tutoring Pipeline."""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.api.v1.endpoints.auth import get_current_user_optional
from app.schemas.pipeline import PipelineExecutionRequest, PipelineExecutionResponse
from app.services.pipeline_orchestrator import pipeline_orchestrator
from app.services.tutor_engine import TutorGenerationError
from app.core.file_security import validate_file_security

router = APIRouter()


@router.post(
    "/execute",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute full end-to-end tutoring pipeline on text input"
)
async def execute_pipeline(
    request: PipelineExecutionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PipelineExecutionResponse:
    """Executes complete workflow:
    Input detection → Question extraction → Classification → RAG retrieval → SymPy solving →
    Answer validation → Markdown formatting → Neural TTS voice → Synchronized subtitles.
    """
    try:
        return await pipeline_orchestrator.execute(
            request=request,
            db=db,
            user_id=current_user.id if current_user else None,
        )
    except HTTPException:
        raise
    except TutorGenerationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"End-to-End pipeline execution failed: {str(e)}"
        )


@router.post(
    "/execute-file",
    response_model=PipelineExecutionResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute full end-to-end tutoring pipeline on uploaded multimodal file"
)
async def execute_pipeline_file(
    file: UploadFile = File(...),
    session_id: Optional[str] = Form(None),
    subject: Optional[str] = Form(None),
    level: Optional[str] = Form("intermediate"),
    preferred_voice: Optional[str] = Form("en-US-AriaNeural"),
    playback_speed: Optional[float] = Form(1.0),
    synthesize_voice: Optional[bool] = Form(True),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> PipelineExecutionResponse:
    """Accepts uploaded image, PDF, DOCX, audio, or video file, extracts questions, executes
    RAG, Socratic tutoring, validation, and synthesizes audio with aligned subtitles."""
    try:
        file_bytes = await file.read()
        category, ext, safe_name = validate_file_security(
            filename=file.filename or "file",
            content_type=file.content_type or "application/octet-stream",
            file_bytes=file_bytes
        )

        request = PipelineExecutionRequest(
            session_id=session_id,
            subject=subject,
            level=level,
            preferred_voice=preferred_voice,
            playback_speed=playback_speed,
            synthesize_voice=synthesize_voice,
            input_type=category
        )

        return await pipeline_orchestrator.execute(
            request=request,
            file_bytes=file_bytes,
            filename=file.filename,
            mime_type=file.content_type,
            db=db,
            user_id=current_user.id if current_user else None,
        )
    except HTTPException:
        raise
    except TutorGenerationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Multimodal pipeline execution failed: {str(e)}"
        )

