"""Pydantic schemas for the Phase 10 Master End-to-End Pipeline Orchestrator."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class PipelineExecutionRequest(BaseModel):
    """Request payload for unified end-to-end educational problem solving."""
    query: Optional[str] = Field(None, description="Raw student text question")
    session_id: Optional[str] = Field(None, description="Optional active study session ID")
    subject: Optional[str] = Field(None, description="Subject domain override or detected topic")
    level: Optional[str] = Field("intermediate", description="Pedagogical explanation rigor: beginner, intermediate, advanced")
    preferred_voice: Optional[str] = Field("en-US-AriaNeural", description="Neural edge-tts voice ID")
    playback_speed: Optional[float] = Field(1.0, description="Speech playback speed: 0.75 to 2.0")
    synthesize_voice: bool = Field(True, description="Whether to generate TTS audio and synchronized subtitles")
    input_type: Optional[str] = Field("text", description="Detected or declared input type: text, image, audio, pdf, docx, video")


class PipelinePerformanceMetrics(BaseModel):
    """Detailed latency profiling across all execution stages."""
    input_processing_time_ms: float = Field(0.0, description="Time to process raw input / OCR / STT")
    query_classification_time_ms: float = Field(0.0, description="Time to classify intent, subject and expansions")
    retrieval_time_ms: float = Field(0.0, description="Hybrid ChromaDB + BM25 search and reranking duration")
    answer_generation_time_ms: float = Field(0.0, description="Socratic reasoning, SymPy solving, and synthesis duration")
    validation_time_ms: float = Field(0.0, description="Hallucination control, citations audit, and consistency verification")
    tts_generation_time_ms: float = Field(0.0, description="Speech normalization, neural TTS audio, and subtitle alignment")
    total_response_time_ms: float = Field(0.0, description="Complete end-to-end pipeline execution time")


class PipelineExecutionResponse(BaseModel):
    """Complete end-to-end result encompassing multimodal input, tutoring, validation, and voice."""
    session_id: Optional[str] = None
    input_type: str = Field("text", description="Resolved input modality")
    extracted_question: str = Field(..., description="Normalized inquiry extracted from input")
    detected_math: List[str] = Field(default_factory=list, description="Mathematical formulas identified in query")
    query_intent: str = Field("conceptual_explanation", description="Pedagogical query category")
    subject: str = Field("STEM", description="Identified academic subject")
    retrieved_chunks_count: int = Field(0, description="Number of curriculum chunks retrieved")
    citations: List[Dict[str, Any]] = Field(default_factory=list, description="Verified bibliographic citations")
    sympy_verified: bool = Field(False, description="Whether mathematical calculations were verified by SymPy")
    sympy_result: Optional[str] = Field(None, description="Symbolic math computation output if applicable")
    formatted_markdown: str = Field(..., description="Complete Socratic step-by-step educational answer")
    validation: Dict[str, Any] = Field(default_factory=dict, description="Answer validation, grounding, and confidence data")
    voice: Optional[Dict[str, Any]] = Field(None, description="Synthesized TTS speech URL and synchronized subtitles")
    performance_metrics: PipelinePerformanceMetrics = Field(..., description="Precise execution timings")

