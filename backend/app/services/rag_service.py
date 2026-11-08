"""Orchestrates the complete educational RAG pipeline: Query Processing -> Hybrid Retrieval -> Reranking -> Context Construction -> Grounded Answer & Citations."""

import time
from typing import Optional
from sqlalchemy.orm import Session

from app.schemas.rag import RAGQueryRequest, RAGResponse, RetrievalDiagnosticResponse
from app.services.query_processor import query_processor
from app.services.rag_retriever import rag_retriever
from app.services.context_builder import context_builder
from app.services.answer_generator import answer_generator


class EducationalRAGService:
    """Master orchestrator executing the 5-stage educational RAG pipeline."""

    def execute_rag(self, request: RAGQueryRequest, db: Session) -> RAGResponse:
        """Run end-to-end RAG pipeline from student question to citation-grounded response."""
        start_time = time.perf_counter()

        # 1. Query Processing
        normalized_q = query_processor.normalize(request.query)
        inferred_subject = request.subject or query_processor.identify_subject(normalized_q)
        intent = query_processor.classify_intent(normalized_q)
        expanded_q = query_processor.expand_query(normalized_q, subject=inferred_subject)

        # Merge explicit metadata filters with query hints
        detected_filters = query_processor.extract_filters(normalized_q)
        academic_level = request.academic_level or detected_filters.get("academic_level")

        # 2. Hybrid Retrieval & Reranking
        retrieved_chunks = rag_retriever.retrieve(
            query=expanded_q,
            db=db,
            subject=inferred_subject,
            academic_level=academic_level,
            source_id=request.source_id,
            top_k=request.top_k,
            enable_hybrid=request.enable_hybrid,
            enable_reranking=request.enable_reranking,
            confidence_threshold=request.confidence_threshold
        )

        # 3. Context Construction
        context_str, citations, is_sufficient = context_builder.build_context(retrieved_chunks)

        # 4. Grounded Answer Synthesis
        answer_text, verified_citations = answer_generator.generate_answer(
            query=normalized_q,
            context_str=context_str,
            citations=citations,
            is_sufficient=is_sufficient,
            subject=inferred_subject
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return RAGResponse(
            query=normalized_q,
            answer=answer_text,
            subject_domain=inferred_subject,
            is_context_sufficient=is_sufficient,
            citations=verified_citations,
            retrieved_chunks_count=len(retrieved_chunks),
            processing_time_ms=round(elapsed_ms, 2),
            intent=intent
        )

    def retrieve_diagnostics(self, request: RAGQueryRequest, db: Session) -> RetrievalDiagnosticResponse:
        """Execute standalone retrieval without LLM answer generation for pipeline diagnostics."""
        normalized_q = query_processor.normalize(request.query)
        inferred_subject = request.subject or query_processor.identify_subject(normalized_q)
        expanded_q = query_processor.expand_query(normalized_q, subject=inferred_subject)
        detected_filters = query_processor.extract_filters(normalized_q)
        academic_level = request.academic_level or detected_filters.get("academic_level")

        chunks = rag_retriever.retrieve(
            query=expanded_q,
            db=db,
            subject=inferred_subject,
            academic_level=academic_level,
            source_id=request.source_id,
            top_k=request.top_k,
            enable_hybrid=request.enable_hybrid,
            enable_reranking=request.enable_reranking,
            confidence_threshold=request.confidence_threshold
        )

        return RetrievalDiagnosticResponse(
            query=normalized_q,
            expanded_query=expanded_q,
            subject_domain=inferred_subject,
            total_candidates=len(chunks),
            chunks=chunks
        )


rag_service = EducationalRAGService()
