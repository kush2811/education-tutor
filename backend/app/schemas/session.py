"""Pydantic schemas for tutoring sessions and messages."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageBase(BaseModel):
    """Base schema for session message."""
    sender_role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content_type: str = Field("text", description="Type: 'text', 'image', 'audio', or 'multimodal'")
    content: str = Field(..., description="Text content or transcription")
    metadata_json: Optional[str] = Field(None, description="Serialized JSON metadata")


class MessageCreate(MessageBase):
    """Schema for sending a new message into a session."""
    pass


class MessageResponse(MessageBase):
    """Schema for returning a session message."""
    id: str
    session_id: str
    created_at: datetime

    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    """Schema for creating a new study session."""
    student_id: Optional[str] = Field("default_student", description="Unique student identifier")
    title: Optional[str] = Field("New Tutoring Session", description="Session title")
    subject: Optional[str] = Field("General STEM", description="Subject or topic of study")


class SessionUpdate(BaseModel):
    """Schema for updating a session."""
    title: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for returning session details."""
    id: str
    student_id: str
    title: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
