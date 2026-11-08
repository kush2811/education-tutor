"""Endpoints for managing student tutoring sessions, conversation history, and privacy-protected access."""

import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select

from app.db.session import get_db
from app.models.user import User
from app.models.session import StudySession, SessionMessage
from app.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionUpdate,
    MessageCreate,
    MessageResponse,
)
from app.api.v1.endpoints.auth import get_current_user_optional
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
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> SessionResponse:
    """Initialize a new tutoring session linked to authenticated student if signed in."""
    user_id = current_user.id if current_user else None
    student_id = current_user.id if current_user else (payload.student_id or "default_student")

    new_session = StudySession(
        user_id=user_id,
        student_id=student_id,
        title=payload.title or "New Tutoring Session",
        subject=payload.subject or "General STEM",
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    logger.info(f"Created study session: id={new_session.id}, user_id={user_id}, title='{new_session.title}'")

    return SessionResponse(
        id=new_session.id,
        user_id=new_session.user_id,
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
    summary="List all study sessions with privacy filtering"
)
def list_sessions(
    student_id: str = "default_student",
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> List[SessionResponse]:
    """Retrieve all study sessions for authenticated student or isolated guest namespace."""
    if current_user:
        # Authenticated student sees their own sessions
        query = (
            select(StudySession)
            .where((StudySession.user_id == current_user.id) | (StudySession.student_id == current_user.id))
            .options(selectinload(StudySession.messages))
            .order_by(StudySession.updated_at.desc())
        )
    else:
        # Unauthenticated guest only sees guest sessions without private user ownership
        query = (
            select(StudySession)
            .where((StudySession.student_id == student_id) & (StudySession.user_id.is_(None)))
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
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> SessionResponse:
    """Retrieve full details and dialogue history with privacy verification."""
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

    # Privacy Check: User cannot access another user's session
    if session.user_id:
        if not current_user or current_user.id != session.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this private study session."
            )

    return session


@router.put(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    summary="Rename or update study session"
)
def update_session(
    session_id: str,
    payload: SessionUpdate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> SessionResponse:
    """Rename conversation title, change subject, or update status with ownership verification."""
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

    # Privacy Check: Ownership verification
    if session.user_id:
        if not current_user or current_user.id != session.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this study session."
            )

    if payload.title is not None:
        session.title = payload.title.strip()
    if payload.subject is not None:
        session.subject = payload.subject.strip()
    if payload.status is not None:
        session.status = payload.status.strip()

    db.commit()
    db.refresh(session)
    logger.info(f"Updated session '{session.id}': new title='{session.title}'")
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
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """Record a user or tutor message with structured input_type, question, and audio references."""
    query = select(StudySession).where(StudySession.id == session_id)
    session = db.execute(query).scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session '{session_id}' not found."
        )

    # Privacy Check: Ownership verification
    if session.user_id:
        if not current_user or current_user.id != session.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to append messages to this study session."
            )

    message = SessionMessage(
        session_id=session_id,
        sender_role=payload.sender_role,
        content_type=payload.content_type,
        content=payload.content,
        input_type=payload.input_type or "text",
        extracted_question=payload.extracted_question,
        audio_url=payload.audio_url,
        citations_json=payload.citations_json,
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
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """Delete a session and all associated dialogue history with ownership verification."""
    query = select(StudySession).where(StudySession.id == session_id)
    session = db.execute(query).scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Study session '{session_id}' not found."
        )

    # Privacy Check: Ownership verification
    if session.user_id:
        if not current_user or current_user.id != session.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this study session."
            )

    db.delete(session)
    db.commit()
    return None
