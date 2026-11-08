"""ORM models for student tutoring sessions and messages."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class StudySession(Base):
    """Represents a student's tutoring session."""
    __tablename__ = "study_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    student_id: Mapped[str] = mapped_column(String(64), index=True, default="default_student")
    title: Mapped[str] = mapped_column(String(255), default="New Tutoring Session")
    subject: Mapped[str] = mapped_column(String(100), default="General STEM")
    status: Mapped[str] = mapped_column(String(30), default="active") # active, completed, archived
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages: Mapped[list["SessionMessage"]] = relationship(
        "SessionMessage", back_populates="session", cascade="all, delete-orphan", order_by="SessionMessage.created_at"
    )


class SessionMessage(Base):
    """Represents an individual message exchanged in a study session."""
    __tablename__ = "session_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("study_sessions.id", ondelete="CASCADE"), index=True)
    sender_role: Mapped[str] = mapped_column(String(20)) # "user", "assistant", "system"
    content_type: Mapped[str] = mapped_column(String(20), default="text") # "text", "image", "audio", "multimodal"
    content: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=True) # JSON metadata for hints, formulas, audio urls
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["StudySession"] = relationship("StudySession", back_populates="messages")
