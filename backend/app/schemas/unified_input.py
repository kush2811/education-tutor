"""Pydantic schemas for the unified multimodal input pipeline."""

from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class SourceReference(BaseModel):
    """Reference anchor inside an educational document, audio, or video."""
    ref_type: str = Field(..., description="'page' or 'timestamp'")
    page_number: Optional[int] = Field(None, description="Page number for PDF/DOCX")
    timestamp_sec: Optional[float] = Field(None, description="Start timestamp in seconds for audio/video")
    end_timestamp_sec: Optional[float] = Field(None, description="End timestamp in seconds")
    label: Optional[str] = Field(None, description="Chapter, section heading, or slide title")
    excerpt: Optional[str] = Field(None, description="Surrounding contextual excerpt")


class SourceFileInfo(BaseModel):
    """Metadata regarding an uploaded source asset."""
    file_name: str
    file_type: str  # "image", "pdf", "docx", "audio", "video", "text"
    file_size_bytes: int
    mime_type: str
    file_path: Optional[str] = None
    asset_id: Optional[str] = None


class UnifiedQuestionPayload(BaseModel):
    """Common structured question representation produced by ALL input types."""
    input_type: str = Field(..., description="'text' | 'image' | 'pdf' | 'docx' | 'audio' | 'video'")
    extracted_question: str = Field(..., description="The core extracted question for Socratic guidance")
    extracted_context: str = Field("", description="Background context, surrounding equations, or frame descriptions")
    math_expressions: List[str] = Field(default_factory=list, description="Extracted LaTeX math formulas")
    source_file: Optional[SourceFileInfo] = Field(None, description="Source file information if file-based")
    references: List[SourceReference] = Field(default_factory=list, description="Page numbers or video timestamps")
    processing_status: str = Field("success", description="'success' | 'partial' | 'error'")
    error_detail: Optional[str] = Field(None, description="Description of any errors encountered")
    confidence_score: float = Field(1.0, ge=0.0, le=1.0, description="Confidence of OCR / transcription")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional processor-specific metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TextProcessRequest(BaseModel):
    """Request model for pure text or formula inquiry."""
    text: str = Field(..., min_length=1, max_length=65536, description="Student typed question")
    session_id: Optional[str] = None


class AudioTranscriptionResponse(BaseModel):
    """Response returned after processing a student recorded audio inquiry."""
    transcript: str
    duration_sec: float
    confidence_score: float
    detected_language: str = "en"
    audio_file_name: str

