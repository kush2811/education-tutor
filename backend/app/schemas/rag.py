"""Pydantic schemas for Phase 5: Retrieval-Augmented Generation (RAG)."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class RAGQueryRequest(BaseModel):
    """Student inquiry request for curriculum-grounded answer generation."""
    query: str = Field(..., min_length=2, max_length=2000, description="Student question or STEM problem")
    subject: Optional[str] = Field(None, description="Optional subject domain filter (e.g. Mathematics, Physics)")
    academic_level: Optional[str] = Field(None, description="Optional academic grade/level filter")
    source_id: Optional[str] = Field(None, description="Optional constraint to a specific registered source")
    top_k: int = Field(default=5, ge=1, le=15, description="Number of curriculum excerpts to retrieve")
    enable_hybrid: bool = Field(default=True, description="Enable hybrid retrieval (Dense Semantic + BM25)")
    enable_reranking: bool = Field(default=True, description="Enable cross-score reranking")
    confidence_threshold: float = Field(default=0.25, ge=0.0, le=1.0, description="Minimum relevance score threshold")


class RAGCitation(BaseModel):
    """Verified, authentic curriculum citation."""
    source_id: str
    source_name: str
    source_url: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: int = 1
    authority: str
    license_type: str
    citation_label: str = Field(..., description="Footnote label e.g. [1]")
    citation_text: str = Field(..., description="Formatted bibliographic citation string")
    excerpt: str = Field(..., description="Verbatim curriculum snippet used to support the answer")


class RAGResponse(BaseModel):
    """Curriculum-grounded educational tutor response."""
    query: str
    answer: str
    subject_domain: str
    is_context_sufficient: bool
    citations: List[RAGCitation]
    retrieved_chunks_count: int
    processing_time_ms: float
    intent: str
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Phase 7 answer validation and hallucination audit")


class RetrievedChunkItem(BaseModel):
    """A retrieved curriculum chunk with relevance and retrieval diagnostics."""
    chunk_id: str
    document_id: str
    source_id: str
    source_name: str
    source_url: str
    authority: str
    license_type: str
    chapter: Optional[str] = None
    section: Optional[str] = None
    page_number: int = 1
    content: str
    extracted_math: List[str] = Field(default_factory=list)
    dense_score: float
    bm25_score: float
    combined_score: float
    rerank_score: float


class RetrievalDiagnosticResponse(BaseModel):
    """Response returned by the standalone retrieval diagnostic endpoint."""
    query: str
    expanded_query: str
    subject_domain: str
    total_candidates: int
    chunks: List[RetrievedChunkItem]


class RAGEvaluationSampleResult(BaseModel):
    """Evaluation result for an individual benchmark question."""
    question_id: str
    question: str
    subject: str
    expected_sources: List[str]
    retrieved_sources: List[str]
    recall_at_k: float
    relevance_score: float
    is_context_sufficient: bool
    expected_context_found: bool
    latency_ms: float
    sample_passed: bool


class RAGEvaluationReport(BaseModel):
    """Comprehensive benchmark evaluation report for the RAG pipeline."""
    total_samples: int
    mean_retrieval_relevance: float
    mean_recall_at_k: float
    citation_precision: float
    uncertainty_accuracy: float
    mean_latency_ms: float
    results: List[RAGEvaluationSampleResult]
