"""Endpoints for managing student tutoring sessions and conversation history."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.db.session import get_db
from app.models.session import StudySession, SessionMessage
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    MessageCreate,
    MessageResponse,
)
from app.core.logging import logger

router = APIRouter()


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new study session"
)
def create_session(
    payload: SessionCreate,
    db: Session = Depends(get_db)
) -> SessionResponse:
    """Initialize a new tutoring session for a student."""
    new_session = StudySession(
        student_id=payload.student_id or "default_student",
        title=payload.title or "New Tutoring Session",
        subject=payload.subject or "General STEM",
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info(f"Created study session: id={new_session.id}, title='{new_session.title}'")

    return SessionResponse(
        id=new_session.id,
        student_id=new_session.student_id,
        title=new_session.title,
        subject=new_session.subject,
        status=new_session.status,
        created_at=new_session.created_at,
        updated_at=new_session.updated_at,
        messages=[]
    )


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="List all study sessions"
)
def list_sessions(
    student_id: str = "default_student",
    db: Session = Depends(get_db)
) -> List[SessionResponse]:
    """Retrieve all study sessions for a given student."""
    query = (
        select(StudySession)
        .where(StudySession.student_id == student_id)
        .options(selectinload(StudySession.messages))
        .order_by(StudySession.updated_at.desc())
    )
    result = db.execute(query)
    sessions = result.scalars().all()
    return list(sessions)


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Get session details and message history"
)
def get_session(
    session_id: str,
    db: Session = Depends(get_db)
) -> SessionResponse:
    """Retrieve full details and dialogue history for a specific session."""
    query = (
        select(StudySession)
        .where(StudySession.id == session_id)
        .options(selectinload(StudySession.messages))
    )
    result = db.execute(query)
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session '{session_id}' not found."
        )

    return session


@router.post(
    "/sessions/{session_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Append a message to a session"
)
def add_message(
    session_id: str,
    payload: MessageCreate,
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Record a user or tutor message within an existing session."""
    query = select(StudySession).where(StudySession.id == session_id)
    session = db.execute(query).scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session '{session_id}' not found."
        )

    message = SessionMessage(
        session_id=session_id,
        sender_role=payload.sender_role,
        content_type=payload.content_type,
        content=payload.content,
        metadata_json=payload.metadata_json,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a study session"
)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """Delete a session and all its associated conversation records."""
    query = select(StudySession).where(StudySession.id == session_id)
    session = db.execute(query).scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session '{session_id}' not found."
        )

    db.delete(session)
    db.commit()
    return None
