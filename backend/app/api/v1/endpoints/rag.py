"""API endpoints for Phase 5: Educational RAG pipeline, hybrid retrieval, and benchmarking."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rag import (
    RAGQueryRequest,
    RAGResponse,
    RetrievalDiagnosticResponse,
    RAGEvaluationReport,
)
from app.services.rag_service import rag_service
from app.services.rag_evaluator import rag_evaluator

router = APIRouter()


@router.post(
    "/query",
    response_model=RAGResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate curriculum-grounded Socratic explanation with verified citations"
)
def execute_curriculum_rag(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
) -> RAGResponse:
    """Accepts a student inquiry or structured question payload, executes hybrid retrieval
    (ChromaDB Dense + BM25 Sparse), reranks candidates, constructs curriculum context, and
    synthesizes a grounded answer with authentic citations."""
    try:
        return rag_service.execute_rag(request=request, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG execution failed: {str(e)}"
        )


@router.post(
    "/retrieve",
    response_model=RetrievalDiagnosticResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve and rerank candidate curriculum chunks for diagnostic inspection"
)
def retrieve_curriculum_candidates(
    request: RAGQueryRequest,
    db: Session = Depends(get_db)
) -> RetrievalDiagnosticResponse:
    """Performs query processing, dense and sparse retrieval, Reciprocal Rank Fusion, and
    cross-encoder scoring without calling the LLM generator."""
    try:
        return rag_service.retrieve_diagnostics(request=request, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retrieval diagnostics failed: {str(e)}"
        )


@router.post(
    "/evaluate",
    response_model=RAGEvaluationReport,
    status_code=status.HTTP_200_OK,
    summary="Execute benchmark evaluation measuring retrieval recall, precision, citations, and latency"
)
def evaluate_rag_pipeline(
    db: Session = Depends(get_db)
) -> RAGEvaluationReport:
    """Executes automated benchmark tests across STEM inquiries and out-of-corpus probe questions,
    reporting recall@k, citation validity, uncertainty accuracy, and latency."""
    try:
        return rag_evaluator.run_benchmark(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG benchmark evaluation failed: {str(e)}"
        )
