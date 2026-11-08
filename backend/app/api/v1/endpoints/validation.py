"""FastAPI endpoints for Phase 7: Answer Validation and Hallucination Control."""

from typing import List, Optional
from fastapi import APIRouter, status, HTTPException
from pydantic import BaseModel, Field

from app.schemas.validation import (
    AnswerValidationRequest,
    AnswerValidationResult,
    CitationValidationItem,
    SourceConflict,
    AnswerConsistencyResult
)
from app.schemas.rag import RAGCitation, RetrievedChunkItem
from app.services.answer_validator import answer_validator
from app.services.citation_validator import citation_validator
from app.services.source_conflict_detector import source_conflict_detector
from app.services.answer_consistency_checker import answer_consistency_checker

router = APIRouter()


class CitationAuditRequest(BaseModel):
    answer: str = Field(..., description="Answer text containing citation markers e.g. [1]")
    citations: List[RAGCitation] = Field(default_factory=list)
    retrieved_chunks: Optional[List[RetrievedChunkItem]] = None


class CitationAuditResponse(BaseModel):
    audit_items: List[CitationValidationItem]
    sanitized_answer: str
    warnings: List[str]


class ConflictAuditRequest(BaseModel):
    chunks: List[RetrievedChunkItem] = Field(..., min_items=1)


class ConsistencyAuditRequest(BaseModel):
    question: str
    answer: str
    code_snippets: Optional[List[str]] = None


@router.post(
    "/validate-answer",
    response_model=AnswerValidationResult,
    status_code=status.HTTP_200_OK,
    summary="Validate AI educational answer for grounding, citation integrity, and consistency"
)
def validate_answer(request: AnswerValidationRequest):
    """Intermediary validation layer executing source-grounding checks, citation validation,

    conflict resolution, and consistency auditing before final student presentation.
    """
    try:
        return answer_validator.validate_answer(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Answer validation failed: {str(e)}"
        )


@router.post(
    "/check-citations",
    response_model=CitationAuditResponse,
    status_code=status.HTTP_200_OK,
    summary="Standalone verification of citation markers, documents, page numbers, and URLs"
)
def check_citations(request: CitationAuditRequest):
    """Audit citation references in answer text against retrieved curriculum context."""
    audit_items, sanitized_text, warnings = citation_validator.validate_citations(
        answer=request.answer,
        citations=request.citations,
        retrieved_chunks=request.retrieved_chunks
    )
    return CitationAuditResponse(
        audit_items=audit_items,
        sanitized_answer=sanitized_text,
        warnings=warnings
    )


@router.post(
    "/check-conflicts",
    response_model=List[SourceConflict],
    status_code=status.HTTP_200_OK,
    summary="Standalone detection of contradictions among retrieved curriculum sources"
)
def check_conflicts(request: ConflictAuditRequest):
    """Detect and resolve factual or conventional discrepancies across retrieved curriculum excerpts."""
    return source_conflict_detector.detect_conflicts(request.chunks)


@router.post(
    "/check-consistency",
    response_model=AnswerConsistencyResult,
    status_code=status.HTTP_200_OK,
    summary="Standalone audit of question relevance, math consistency via SymPy, and code safety via AST"
)
def check_consistency(request: ConsistencyAuditRequest):
    """Audit internal logical consistency, mathematical derivations, and programming snippet safety."""
    return answer_consistency_checker.check_consistency(
        question=request.question,
        answer=request.answer,
        code_snippets=request.code_snippets
    )

