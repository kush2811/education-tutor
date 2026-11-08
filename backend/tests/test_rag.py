"""Automated unit test suite for Phase 5: Retrieval-Augmented Generation (RAG)."""

import os
import tempfile
import pytest
from sqlalchemy.orm import Session

from app.models.knowledge import EducationalSource, KnowledgeDocument
from app.services.knowledge_sources import seed_default_sources
from app.services.knowledge_manager import knowledge_manager
from app.services.query_processor import query_processor
from app.services.rag_retriever import rag_retriever
from app.services.context_builder import context_builder
from app.services.answer_generator import answer_generator
from app.services.rag_service import rag_service
from app.services.rag_evaluator import rag_evaluator
from app.schemas.rag import RAGQueryRequest


@pytest.fixture(scope="function")
def seeded_curriculum(db_session: Session):
    """Seed default sources and index foundational STEM curriculum chapters."""
    seed_default_sources(db_session)

    docs_to_seed = [
        # 1. Physics Chapter
        (
            "ncert-physics-class11",
            "Chapter 4: Laws of Motion",
            (
                "# Chapter 4: Laws of Motion\n\n"
                "## 4.1 First Law of Motion\n"
                "An object continues to be in a state of rest or of uniform motion in a straight line unless acted upon by a net external force.\n\n"
                "## 4.2 Second Law of Motion\n"
                "The rate of change of momentum of a body is directly proportional to the applied force: $$F = ma$$.\n"
                "Where $F$ is force in Newtons, $m$ is inertial mass, and $a$ is acceleration.\n\n"
                "## 4.3 Third Law of Motion\n"
                "To every action, there is an equal and opposite reaction.\n"
            )
        ),
        # 2. Mathematics Chapter
        (
            "ncert-math-class10",
            "Chapter 4: Quadratic Equations and Trigonometry",
            (
                "# Chapter 4: Quadratic Equations and Trigonometry\n\n"
                "## 4.1 Quadratic Formula\n"
                "A quadratic equation in standard form is $ax^2 + bx + c = 0$ where $a \\neq 0$.\n"
                "The roots are given by the quadratic formula: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$.\n"
                "The discriminant is $D = b^2 - 4ac$.\n\n"
                "## 4.2 Trigonometric Identity\n"
                "The fundamental Pythagorean trigonometric identity relates sine and cosine: $$\\sin^2(\\theta) + \\cos^2(\\theta) = 1$$.\n"
            )
        ),
        # 3. Chemistry Chapter
        (
            "ncert-chemistry-class12",
            "Chapter 4: Chemical Bonding",
            (
                "# Chapter 4: Chemical Bonding\n\n"
                "## 4.1 Covalent Bonding\n"
                "A covalent bond is formed by the mutual sharing of one or more pairs of electrons between two atoms.\n\n"
                "## 4.2 Ionic Bonding\n"
                "An ionic bond is formed by the complete transfer of one or more valence electrons from an electropositive atom to an electronegative atom.\n"
            )
        ),
        # 4. Computer Science Chapter
        (
            "python-docs-312",
            "Algorithms: Binary Search in Sorted Arrays",
            (
                "# Algorithms: Binary Search\n\n"
                "Binary search is an efficient search algorithm that finds the position of a target value within a sorted array.\n"
                "It operates via divide and conquer with a time complexity of $O(\\log n)$.\n"
            )
        ),
    ]

    for source_id, title, content in docs_to_seed:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(content)
            temp_file = f.name
        try:
            knowledge_manager.add_document(
                source_id=source_id,
                file_path=temp_file,
                title=title,
                db=db_session
            )
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    return db_session


def test_query_processor():
    """Verify query normalization, classification, expansion, and filter detection."""
    # 1. Normalization
    raw = "What is the formula for   \\[F = ma\\]   in physics?  "
    norm = query_processor.normalize(raw)
    assert "$$F = ma$$" in norm
    assert "  " not in norm

    # 2. Subject identification
    assert query_processor.identify_subject("calculate the derivative and limit of function") == "Mathematics"
    assert query_processor.identify_subject("what is momentum, acceleration and force") == "Physics"
    assert query_processor.identify_subject("explain covalent bonds and valence electrons") == "Chemistry"
    assert query_processor.identify_subject("binary search algorithm in python array") == "Computer Science"

    # 3. Intent classification
    assert query_processor.classify_intent("Define Newton's first law") == "definition"
    assert query_processor.classify_intent("What is the formula for kinetic energy") == "formula_lookup"
    assert query_processor.classify_intent("How to solve quadratic equations step by step") == "step_by_step_solution"

    # 4. Expansion
    expanded = query_processor.expand_query("Newton's second law", subject="Physics")
    assert "force" in expanded.lower() or "acceleration" in expanded.lower() or "f = ma" in expanded.lower()

    # 5. Filter extraction
    filters = query_processor.extract_filters("Explain kinematics for Class 11 students")
    assert filters.get("academic_level") == "Higher Secondary (Grade 11)"


def test_hybrid_retrieval_and_reranking(seeded_curriculum: Session):
    """Verify dense + sparse retrieval, Reciprocal Rank Fusion, and reranking."""
    results = rag_retriever.retrieve(
        query="What is Newton's second law of motion and F = ma?",
        db=seeded_curriculum,
        subject="Physics",
        top_k=3,
        enable_hybrid=True,
        enable_reranking=True,
        confidence_threshold=0.30
    )

    assert len(results) >= 1
    top_match = results[0]
    assert "ncert-physics-class11" in top_match.source_id
    assert "NCERT Class 11 Physics" in top_match.source_name
    assert top_match.dense_score > 0.0
    assert top_match.rerank_score >= 0.30
    assert "$$F = ma$$" in top_match.content or "Second Law" in top_match.content


def test_context_construction_and_citations(seeded_curriculum: Session):
    """Verify reference card construction and citation metadata formatting."""
    results = rag_retriever.retrieve(
        query="rate of change of momentum",
        db=seeded_curriculum,
        subject="Physics",
        top_k=2
    )

    context_str, citations, is_sufficient = context_builder.build_context(results)
    assert is_sufficient is True
    assert len(citations) >= 1

    first_cit = citations[0]
    assert first_cit.citation_label == "[1]"
    assert "NCERT" in first_cit.source_name
    assert first_cit.source_url.startswith("http")
    assert "Page 1" in first_cit.citation_text
    assert "[1] SOURCE:" in context_str


def test_grounded_answer_generation_and_uncertainty(seeded_curriculum: Session):
    """Test grounded answer generation on in-corpus query vs uncertainty on unindexed query."""
    # 1. In-corpus inquiry: Context is sufficient
    results = rag_retriever.retrieve(
        query="Explain Newton's second law",
        db=seeded_curriculum,
        subject="Physics",
        top_k=2
    )
    context_str, citations, is_sufficient = context_builder.build_context(results)

    ans_text, ans_citations = answer_generator.generate_answer(
        query="Explain Newton's second law",
        context_str=context_str,
        citations=citations,
        is_sufficient=is_sufficient,
        subject="Physics"
    )

    assert len(ans_citations) >= 1
    assert "NCERT" in ans_text or "[1]" in ans_text
    assert "Key Takeaways" in ans_text

    # 2. Missing inquiry: Context is insufficient -> must communicate uncertainty without hallucinating
    empty_context, empty_citations, empty_sufficient = context_builder.build_context([])
    assert empty_sufficient is False

    uncertain_ans, no_cits = answer_generator.generate_answer(
        query="What happened during the Punic wars in 264 BC?",
        context_str=empty_context,
        citations=empty_citations,
        is_sufficient=empty_sufficient,
        subject="History"
    )

    assert len(no_cits) == 0
    assert "insufficient" in uncertain_ans.lower()
    assert "curriculum context" in uncertain_ans.lower()


def test_rag_service_end_to_end(seeded_curriculum: Session):
    """Verify end-to-end RAG service pipeline execution."""
    req = RAGQueryRequest(
        query="State Newton's third law of motion",
        subject="Physics",
        top_k=3
    )

    response = rag_service.execute_rag(req, db=seeded_curriculum)
    assert response.is_context_sufficient is True
    assert len(response.citations) >= 1
    assert response.processing_time_ms > 0
    assert response.subject_domain == "Physics"
    assert "action" in response.answer.lower() or "reaction" in response.answer.lower()


def test_rag_evaluator_benchmark(seeded_curriculum: Session):
    """Verify automated benchmark evaluation measuring recall, precision, citations, and latency."""
    report = rag_evaluator.run_benchmark(db=seeded_curriculum)

    assert report.total_samples == 6
    assert report.citation_precision == 1.0  # 100% zero fake citations
    assert report.uncertainty_accuracy >= 0.80
    assert report.mean_latency_ms > 0
    assert len(report.results) == 6


def test_rag_api_endpoints(client, seeded_curriculum: Session):
    """Test REST API endpoints for RAG query, diagnostics retrieval, and evaluation."""
    # 1. POST /api/v1/rag/query
    res = client.post("/api/v1/rag/query", json={
        "query": "What is Newton's second law of motion?",
        "subject": "Physics",
        "top_k": 3
    })
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["is_context_sufficient"] is True
    assert len(res_json["citations"]) >= 1
    assert "NCERT" in res_json["citations"][0]["source_name"]

    # 2. POST /api/v1/rag/retrieve (diagnostics)
    diag_res = client.post("/api/v1/rag/retrieve", json={
        "query": "momentum and force",
        "subject": "Physics"
    })
    assert diag_res.status_code == 200
    diag_json = diag_res.json()
    assert diag_json["total_candidates"] >= 1
    assert "f = ma" in diag_json["chunks"][0]["content"].lower()

    # 3. POST /api/v1/rag/evaluate
    eval_res = client.post("/api/v1/rag/evaluate")
    assert eval_res.status_code == 200
    eval_json = eval_res.json()
    assert eval_json["total_samples"] == 6
    assert eval_json["citation_precision"] == 1.0
