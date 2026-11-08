"""Pydantic schemas for Phase 7: Answer Validation and Hallucination Control."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.schemas.rag import RAGCitation, RetrievedChunkItem


class GroundingStatus(str, Enum):
    """Categorical grounding classification avoiding pseudo-scientific percentage claims."""
    SUPPORTED_BY_SOURCES = "supported_by_sources"
    GENERAL_MODEL_KNOWLEDGE = "general_model_knowledge"
    INSUFFICIENTLY_VERIFIED = "insufficiently_verified"


class CitationCheckStatus(str, Enum):
    """Integrity status for individual citations."""
    VALID = "valid"
    PHANTOM_INDEX = "phantom_index"
    MISMATCHED_DOCUMENT = "mismatched_document"
    INVALID_PAGE = "invalid_page"
    INVALID_URL = "invalid_url"


class CitationValidationItem(BaseModel):
    """Detailed audit for a single citation reference in the answer."""
    citation_label: str = Field(..., description="Citation marker e.g. '[1]'")
    status: CitationCheckStatus
    source_id: Optional[str] = None
    source_name: Optional[str] = None
    page_number: Optional[int] = None
    source_url: Optional[str] = None
    details: str = Field(..., description="Explanation of validation result or discrepancy")


class SourceConflict(BaseModel):
    """Detected contradiction between two retrieved educational excerpts."""
    topic_or_entity: str
    source_a_name: str
    source_a_authority: str
    source_a_claim: str
    source_b_name: str
    source_b_authority: str
    source_b_claim: str
    resolved: bool = False
    preferred_source: Optional[str] = None
    resolution_rationale: str


class FactualClaimCheck(BaseModel):
    """Validation of an individual factual statement against retrieved context."""
    claim_text: str
    is_grounded: bool
    supporting_chunk_id: Optional[str] = None
    supporting_source: Optional[str] = None
    grounding_score: float = Field(default=0.0, ge=0.0, le=1.0)


class AnswerConsistencyResult(BaseModel):
    """Audit of answer relevance, logical continuity, math consistency, and code safety."""
    addresses_question: bool = True
    question_relevance_score: float = Field(default=1.0, ge=0.0, le=1.0)
    logical_flow_valid: bool = True
    calculations_consistent: bool = True
    math_discrepancies: List[str] = Field(default_factory=list)
    code_safe_and_plausible: bool = True
    code_issues: List[str] = Field(default_factory=list)


class AnswerValidationRequest(BaseModel):
    """Request payload to audit and sanitize an AI-generated educational answer."""
    question: str = Field(..., min_length=2, description="Student question or STEM problem")
    answer: str = Field(..., min_length=2, description="Generated answer to be verified")
    retrieved_chunks: List[RetrievedChunkItem] = Field(
        default_factory=list,
        description="Curriculum excerpts retrieved from the knowledge base"
    )
    citations: List[RAGCitation] = Field(
        default_factory=list,
        description="Bibliographic citations referenced in the answer"
    )
    subject: Optional[str] = None
    code_snippets: Optional[List[str]] = Field(
        default=None,
        description="Optional list of code blocks extracted from the answer"
    )


class AnswerValidationResult(BaseModel):
    """Complete validation verdict returned by the validation layer."""
    is_valid: bool = Field(..., description="Overall verdict: whether the answer meets academic safety and grounding standards")
    grounding_status: GroundingStatus
    grounding_explanation: str = Field(..., description="Human-readable explanation of verification tier and evidence")
    factual_claims: List[FactualClaimCheck] = Field(default_factory=list)
    citation_audit: List[CitationValidationItem] = Field(default_factory=list)
    source_conflicts: List[SourceConflict] = Field(default_factory=list)
    consistency: AnswerConsistencyResult
    insufficient_info_detected: bool = False
    insufficient_info_message: Optional[str] = None
    sanitized_answer: str = Field(..., description="Answer with phantom citations or safety issues flagged/sanitized")
    warnings: List[str] = Field(default_factory=list)
    limitations_disclaimer: str = Field(
        default=(
            "Automated verification uses symbolic math checking, static AST code analysis, "
            "and lexical/semantic chunk matching. It does not constitute formal mathematical proof "
            "or accredited peer review."
        )
    )
