"""ORM model for users and student profiles."""

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class User(Base):
    """User account entity representing a student or educator."""
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(150), default="Student Learner")
    grade_level: Mapped[str] = mapped_column(String(50), default="Grade 10") # e.g. "Grade 10", "Grade 12", "Undergraduate"
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions: Mapped[list["StudySession"]] = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")
    assets: Mapped[list["UploadedAsset"]] = relationship("UploadedAsset", back_populates="user", cascade="all, delete-orphan")

