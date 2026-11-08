"""Pydantic schemas for Phase 8: Text-to-Speech and Synchronized Subtitles."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class WordSegment(BaseModel):
    """Timestamped word segment for synchronized subtitle highlighting."""
    word: str
    start_time: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(..., ge=0.0, description="End timestamp in seconds")


class SentenceSegment(BaseModel):
    """Timestamped sentence segment matching display text to spoken audio."""
    sentence_index: int
    display_text: str = Field(..., description="Original markdown/formatted sentence")
    spoken_text: str = Field(..., description="Normalized text spoken by TTS")
    start_time: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end_time: float = Field(..., ge=0.0, description="End timestamp in seconds")
    words: List[WordSegment] = Field(default_factory=list, description="Word-level timestamp segments")


class TTSVoiceRequest(BaseModel):
    """Request to convert educational response into speech with aligned subtitles."""
    text: str = Field(..., min_length=1, max_length=10000, description="Educational answer markdown text")
    voice: str = Field(default="en-US-AriaNeural", description="Neural voice identifier")
    rate: str = Field(default="+0%", description="Speech speed adjustment e.g. '-25%', '+0%', '+25%'")
    pitch: str = Field(default="+0Hz", description="Pitch adjustment")
    include_word_segments: bool = Field(default=True, description="Whether to compute word-level timestamps")


class TTSVoiceResponse(BaseModel):
    """Structured response containing audio file reference and timestamped subtitle segments."""
    complete_answer_text: str
    spoken_text: str
    audio_url: Optional[str] = Field(None, description="URL or endpoint to fetch generated audio file")
    duration_seconds: float = Field(..., ge=0.0, description="Total audio playback duration in seconds")
    sentence_segments: List[SentenceSegment] = Field(default_factory=list)
    voice_used: str
    alignment_method: str = Field(..., description="Timestamp method: 'neural_speech_timestamps' or 'forced_alignment_fallback'")
    audio_format: str = Field(default="mp3", description="Audio container format: 'mp3', 'wav', or 'browser_speech'")
    error: Optional[str] = None


class NormalizeSpeechRequest(BaseModel):
    """Request to inspect speech normalization on educational content without synthesizing audio."""
    text: str = Field(..., min_length=1, description="Markdown answer text")


class NormalizeSpeechResponse(BaseModel):
    """Spoken speech script ready for natural voice narration."""
    original_text: str
    spoken_script: str
    sentence_pairs: List[Dict[str, str]]
