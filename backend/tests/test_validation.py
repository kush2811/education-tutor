"""Comprehensive test suite for Phase 7: Answer Validation and Hallucination Control."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.rag import RAGCitation, RetrievedChunkItem
from app.schemas.validation import (
    AnswerValidationRequest,
    GroundingStatus,
    CitationCheckStatus,
)
from app.services.citation_validator import citation_validator
from app.services.source_grounding_checker import source_grounding_checker
from app.services.source_conflict_detector import source_conflict_detector
from app.services.answer_consistency_checker import answer_consistency_checker
from app.services.answer_validator import answer_validator


@pytest.fixture
def sample_chunk_ncert() -> RetrievedChunkItem:
    return RetrievedChunkItem(
        chunk_id="chunk-ncert-1",
        document_id="doc-ncert-phys",
        source_id="ncert-physics-class11",
        source_name="NCERT Class 11 Physics",
        source_url="https://ncert.nic.in/textbook.php?kepy1=4",
        authority="National Curriculum Body",
        license_type="Fair Dealing (Educational)",
        chapter="Chapter 4",
        section="Section 4.3",
        page_number=73,
        content=(
            "Newton's Second Law of Motion states that the rate of change of momentum of a body "
            "is directly proportional to the applied force and takes place in the direction in which the force acts: F = ma."
        ),
        dense_score=0.92,
        bm25_score=0.88,
        combined_score=0.90,
        rerank_score=0.89
    )


@pytest.fixture
def sample_citation_ncert() -> RAGCitation:
    return RAGCitation(
        source_id="ncert-physics-class11",
        source_name="NCERT Class 11 Physics",
        source_url="https://ncert.nic.in/textbook.php?kepy1=4",
        chapter="Chapter 4",
        section="Section 4.3",
        page_number=73,
        authority="National Curriculum Body",
        license_type="Fair Dealing (Educational)",
        citation_label="[1]",
        citation_text="NCERT Class 11 Physics, Chapter 4, Section 4.3, Page 73 (National Curriculum Body)",
        excerpt="Newton's Second Law of Motion states that the rate of change of momentum..."
    )


def test_correctly_supported_answer_with_valid_citations(sample_chunk_ncert, sample_citation_ncert):
    """Verify that an answer whose factual statements match retrieved curriculum is marked SUPPORTED_BY_SOURCES."""
    question = "State Newton's second law of motion and its formula."
    answer = (
        "According to Newton's Second Law of Motion, the rate of change of momentum is directly proportional "
        "to the applied force and takes place in the direction of the force [1]. "
        "The mathematical formulation is given by: $$F = ma$$."
    )

    req = AnswerValidationRequest(
        question=question,
        answer=answer,
        retrieved_chunks=[sample_chunk_ncert],
        citations=[sample_citation_ncert],
        subject="Physics"
    )

    result = answer_validator.validate_answer(req)

    assert result.is_valid is True
    assert result.grounding_status == GroundingStatus.SUPPORTED_BY_SOURCES
    assert len(result.citation_audit) == 1
    assert result.citation_audit[0].status == CitationCheckStatus.VALID
    assert result.citation_audit[0].source_id == "ncert-physics-class11"
    assert result.consistency.addresses_question is True
    assert result.consistency.calculations_consistent is True
    assert len(result.factual_claims) >= 1
    assert any(c.is_grounded for c in result.factual_claims)


def test_incorrect_and_phantom_citations(sample_chunk_ncert, sample_citation_ncert):
    """Detect phantom citation markers (e.g. [99]) and invalid URLs/pages, sanitizing the answer text."""
    answer = (
        "Force is defined as mass times acceleration [1]. "
        "Quantum gravitational flux implies non-local action [99]."
    )

    # 1. Phantom Citation Check
    audits, sanitized, warnings = citation_validator.validate_citations(
        answer=answer,
        citations=[sample_citation_ncert],
        retrieved_chunks=[sample_chunk_ncert]
    )

    phantom_audits = [a for a in audits if a.status == CitationCheckStatus.PHANTOM_INDEX]
    assert len(phantom_audits) == 1
    assert phantom_audits[0].citation_label == "[99]"
    assert "[99 (Unverified Citation)]" in sanitized
    assert any("Phantom citation detected" in w for w in warnings)

    # 2. Invalid URL Citation Check
    bad_citation = RAGCitation(
        source_id="fake-source",
        source_name="Fake Source",
        source_url="not-a-valid-url",
        page_number=10,
        authority="Unknown",
        license_type="Unknown",
        citation_label="[2]",
        citation_text="Fake Source Page 10",
        excerpt="Some fake excerpt"
    )
    audits2, _, warnings2 = citation_validator.validate_citations(
        answer="Some claim [2]",
        citations=[bad_citation],
        retrieved_chunks=[]
    )
    assert any(a.status == CitationCheckStatus.INVALID_URL for a in audits2)


def test_missing_knowledge_and_insufficient_information():
    """Verify that when curriculum context is missing, the validator flags insufficient info rather than fabricating answers."""
    question = "Explain dark matter interaction with supersymmetric tachyons in detail."
    answer = (
        "The educational knowledge base does not contain enough information on supersymmetric tachyons "
        "to construct a verified academic answer."
    )

    # Run with empty retrieved chunks
    claims, insufficient, msg, ratio = source_grounding_checker.check_grounding(
        answer=answer,
        retrieved_chunks=[]
    )

    assert insufficient is True
    assert msg is not None
    assert "no verified curriculum materials" in msg.lower()
    assert ratio == 0.0

    # Test full validator on missing context
    req = AnswerValidationRequest(
        question=question,
        answer=answer,
        retrieved_chunks=[],
        citations=[]
    )
    res = answer_validator.validate_answer(req)
    assert res.insufficient_info_detected is True
    assert res.grounding_status == GroundingStatus.INSUFFICIENTLY_VERIFIED


def test_conflicting_sources_resolution_hierarchy():
    """Detect conventional conflicts across sources and resolve in favor of higher authority (e.g. NCERT > University OER)."""
    # Chunk A: NCERT Physics (tier weight 100)
    chunk_ncert = RetrievedChunkItem(
        chunk_id="ch-ncert-thermo",
        document_id="doc-ncert",
        source_id="ncert-phys-11",
        source_name="NCERT Class 11 Physics",
        source_url="https://ncert.nic.in/textbook.php?kepy1=12",
        authority="National Curriculum Body",
        license_type="Fair Dealing",
        chapter="Chapter 12",
        section="12.1",
        page_number=305,
        content="In thermodynamics, according to the First Law, ΔU = Q - W where W is the work done by the system.",
        dense_score=0.9,
        bm25_score=0.8,
        combined_score=0.85,
        rerank_score=0.85
    )

    # Chunk B: Chemistry OER (tier weight 70)
    chunk_oer = RetrievedChunkItem(
        chunk_id="ch-oer-thermo",
        document_id="doc-oer",
        source_id="oer-chem",
        source_name="LibreTexts Chemistry",
        source_url="https://chem.libretexts.org/thermodynamics",
        authority="Open Educational Resource",
        license_type="CC BY-NC-SA 4.0",
        chapter="Chapter 5",
        section="5.2",
        page_number=120,
        content="In chemical thermodynamics, the First Law is expressed as ΔU = Q + W where W is the work done on the system.",
        dense_score=0.85,
        bm25_score=0.75,
        combined_score=0.80,
        rerank_score=0.80
    )

    conflicts = source_conflict_detector.detect_conflicts([chunk_ncert, chunk_oer])
    assert len(conflicts) == 1
    c = conflicts[0]
    assert "First Law of Thermodynamics" in c.topic_or_entity
    assert c.resolved is True
    assert c.preferred_source == "NCERT Class 11 Physics"
    assert "tier weight 100" in c.resolution_rationale

    # Test equal tier unresolved conflict
    chunk_mit = RetrievedChunkItem(
        chunk_id="ch-mit",
        document_id="doc-mit",
        source_id="mit-801",
        source_name="MIT Physics 8.01",
        source_url="https://ocw.mit.edu/courses/physics-801",
        authority="Official University Material",
        license_type="CC BY-NC-SA 4.0",
        chapter="Lecture 5",
        section="5",
        page_number=10,
        content="The First Law of Thermodynamics is ΔU = Q - W where work done by the system expands against pressure.",
        dense_score=0.9,
        bm25_score=0.8,
        combined_score=0.85,
        rerank_score=0.85
    )
    chunk_stanford = RetrievedChunkItem(
        chunk_id="ch-stanford",
        document_id="doc-stanford",
        source_id="stanford-chem",
        source_name="Stanford Chemistry OER",
        source_url="https://stanford.edu/oer-chem",
        authority="Official University Material",
        license_type="CC BY-NC-SA 4.0",
        chapter="Unit 3",
        section="3",
        page_number=15,
        content="The First Law of Thermodynamics uses ΔU = Q + W where work done on the system increases internal energy.",
        dense_score=0.88,
        bm25_score=0.78,
        combined_score=0.83,
        rerank_score=0.83
    )

    conflicts_equal = source_conflict_detector.detect_conflicts([chunk_mit, chunk_stanford])
    assert len(conflicts_equal) == 1
    assert conflicts_equal[0].resolved is False
    assert "Unresolved academic convention" in conflicts_equal[0].resolution_rationale


def test_ambiguous_and_irrelevant_questions():
    """Verify that an answer deviating completely from the inquiry is caught by the consistency checker."""
    question = "How does photosynthesis convert solar energy into glucose in plant chloroplasts?"
    off_topic_answer = (
        "To find the derivative of f(x) = x^2, we apply the power rule: "
        "d/dx(x^n) = n*x^(n-1). Therefore, f'(x) = 2*x."
    )

    consistency = answer_consistency_checker.check_consistency(
        question=question,
        answer=off_topic_answer
    )

    assert consistency.addresses_question is False
    assert consistency.question_relevance_score < 0.15


def test_mathematical_consistency_error_detection():
    """Verify that internal calculation errors (e.g. 2 + 3 = 9 or 2*x = 10 with x = 8) are caught by SymPy."""
    answer_with_math_error = (
        "Step 1: Compute intermediate sum:\n"
        "$$2 + 3 = 9$$\n"
        "Step 2: Solve equation:\n"
        "$$2*x = 10$$\n"
        "Therefore, we find that x = 8."
    )

    consistency = answer_consistency_checker.check_consistency(
        question="Calculate value of x",
        answer=answer_with_math_error
    )

    assert consistency.calculations_consistent is False
    assert len(consistency.math_discrepancies) >= 1
    assert any("2 + 3 = 9" in d for d in consistency.math_discrepancies)


def test_programming_safety_and_syntax_error_detection():
    """Verify that unsafe system calls and syntax errors in code examples are intercepted via static AST analysis."""
    # 1. Security violation: os.system call
    unsafe_code_answer = (
        "Here is how to clean up temporary cache files in Python:\n"
        "```python\n"
        "import os\n"
        "def clean_cache():\n"
        "    os.system('rm -rf /')\n"
        "```"
    )

    consistency1 = answer_consistency_checker.check_consistency(
        question="How to delete files in Python?",
        answer=unsafe_code_answer
    )
    assert consistency1.code_safe_and_plausible is False
    assert any("Security policy violation" in issue for issue in consistency1.code_issues)
    assert any("os.system" in issue for issue in consistency1.code_issues)

    # 2. Syntax error in code block
    broken_code_answer = (
        "```python\n"
        "def broken_function(\n"
        "    return 42\n"
        "```"
    )
    consistency2 = answer_consistency_checker.check_consistency(
        question="Define a function in python",
        answer=broken_code_answer
    )
    assert consistency2.code_safe_and_plausible is False
    assert any("syntax error" in issue.lower() for issue in consistency2.code_issues)


def test_confidence_and_transparency_classification():
    """Verify that explanations from model reasoning without indexed curriculum are labeled GENERAL_MODEL_KNOWLEDGE."""
    question = "Explain the intuitive concept of recursion in computer science."
    answer = (
        "Recursion is a programming technique where a function solves a problem by calling a smaller instance of itself. "
        "Every recursive algorithm requires a base case to terminate execution and a recursive step to progress toward it."
    )

    req = AnswerValidationRequest(
        question=question,
        answer=answer,
        retrieved_chunks=[],
        citations=[]
    )

    result = answer_validator.validate_answer(req)
    # Addresses question, math consistent, no code issues -> General Model Knowledge
    assert result.is_valid is True
    assert result.grounding_status == GroundingStatus.GENERAL_MODEL_KNOWLEDGE
    assert "General Model Knowledge" in result.grounding_explanation
    assert result.limitations_disclaimer != ""


def test_validation_api_endpoints(sample_chunk_ncert, sample_citation_ncert):
    """Verify all Phase 7 FastAPI validation endpoints via TestClient."""
    client = TestClient(app)

    # 1. POST /api/v1/validation/validate-answer
    val_payload = {
        "question": "What is Newton's second law?",
        "answer": "Newton's second law states that F = ma [1].",
        "retrieved_chunks": [sample_chunk_ncert.model_dump()],
        "citations": [sample_citation_ncert.model_dump()],
        "subject": "Physics"
    }
    r1 = client.post("/api/v1/validation/validate-answer", json=val_payload)
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["is_valid"] is True
    assert data1["grounding_status"] == "supported_by_sources"

    # 2. POST /api/v1/validation/check-citations
    cit_payload = {
        "answer": "This fact is supported [1], and another [99].",
        "citations": [sample_citation_ncert.model_dump()]
    }
    r2 = client.post("/api/v1/validation/check-citations", json=cit_payload)
    assert r2.status_code == 200
    data2 = r2.json()
    assert len(data2["audit_items"]) == 2
    assert "[99 (Unverified Citation)]" in data2["sanitized_answer"]

    # 3. POST /api/v1/validation/check-conflicts
    conflict_payload = {
        "chunks": [sample_chunk_ncert.model_dump()]
    }
    r3 = client.post("/api/v1/validation/check-conflicts", json=conflict_payload)
    assert r3.status_code == 200
    assert isinstance(r3.json(), list)

    # 4. POST /api/v1/validation/check-consistency
    cons_payload = {
        "question": "Is 2 + 2 equal to 4?",
        "answer": "Yes, mathematically 2 + 2 = 4.",
        "code_snippets": []
    }
    r4 = client.post("/api/v1/validation/check-consistency", json=cons_payload)
    assert r4.status_code == 200
    data4 = r4.json()
    assert data4["addresses_question"] is True
    assert data4["calculations_consistent"] is True
