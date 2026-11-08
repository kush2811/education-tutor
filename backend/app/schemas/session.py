"""Pydantic schemas for tutoring sessions and messages."""

import json
from datetime import datetime
from typing import Optional, List, Any, Union, Dict
from pydantic import BaseModel, Field, field_validator, model_validator


class MessageBase(BaseModel):
    """Base schema for session message."""
    sender_role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content_type: str = Field("text", description="Type: 'text', 'image', 'audio', or 'multimodal'")
    content: str = Field(..., description="Text content or transcription")
    input_type: Optional[str] = Field("text", description="text, image, audio, pdf, docx, video")
    extracted_question: Optional[str] = Field(None, description="Normalized inquiry statement")
    audio_url: Optional[str] = Field(None, description="Synthesized TTS audio reference link")
    citations_json: Optional[Union[str, List[Any], Dict[str, Any]]] = Field(None, description="Serialized bibliographic citations")
    metadata_json: Optional[Union[str, List[Any], Dict[str, Any]]] = Field(None, description="Serialized JSON metadata")

    @field_validator("citations_json", "metadata_json", mode="before")
    @classmethod
    def serialize_json_fields(cls, v):
        if isinstance(v, (list, dict)):
            return json.dumps(v)
        return v


class MessageCreate(MessageBase):
    """Schema for sending a new message into a session."""
    pass


class MessageResponse(MessageBase):
    """Schema for returning a session message."""
    id: str
    session_id: str
    citations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def populate_citations(self):
        if self.citations_json and not self.citations:
            try:
                if isinstance(self.citations_json, str):
                    self.citations = json.loads(self.citations_json)
                elif isinstance(self.citations_json, list):
                    self.citations = self.citations_json
            except Exception:
                self.citations = None
        return self


class SessionCreate(BaseModel):
    """Schema for creating a new study session."""
    student_id: Optional[str] = Field("default_student", description="Unique student identifier")
    title: Optional[str] = Field("New Tutoring Session", description="Session title")
    subject: Optional[str] = Field("General STEM", description="Subject or topic of study")


class SessionUpdate(BaseModel):
    """Schema for updating/renaming a session."""
    title: Optional[str] = None
    subject: Optional[str] = None
    status: Optional[str] = None


class SessionResponse(BaseModel):
    """Schema for returning session details."""
    id: str
    user_id: Optional[str] = None
    student_id: str
    title: str
    subject: str
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True
