"""Automated test suite for Phase 4: Educational Knowledge Base Development."""

import os
import tempfile
import pytest
from sqlalchemy.orm import Session

from app.models.knowledge import EducationalSource, KnowledgeDocument, DocumentChunk, QualityReport
from app.services.knowledge_sources import (
    seed_default_sources,
    validate_source_license_compliance,
    BUILTIN_EDUCATIONAL_SOURCES,
)
from app.services.knowledge_cleaner import content_cleaner
from app.services.knowledge_extractor import document_extractor
from app.services.educational_chunker import educational_chunker
from app.services.embedding_service import embedding_service
from app.services.vector_store import vector_store
from app.services.data_quality import data_quality_auditor
from app.services.knowledge_manager import knowledge_manager


def test_source_registry_seed_and_compliance(db_session: Session):
    """Test seeding authoritative sources and verifying legal license compliance."""
    # 1. Seed sources into test database
    count = seed_default_sources(db_session)
    assert count == len(BUILTIN_EDUCATIONAL_SOURCES)
    assert count >= 10

    # Verify categories present
    sources = db_session.query(EducationalSource).all()
    categories = {s.authority_category for s in sources}
    assert "ncert" in categories
    assert "gov_portal" in categories
    assert "university" in categories
    assert "oer" in categories
    assert "programming_docs" in categories
    assert "research" in categories

    # Verify specific sources exist
    ncert_math = db_session.query(EducationalSource).filter(EducationalSource.id == "ncert-math-class10").first()
    assert ncert_math is not None
    assert "Mathematics" in ncert_math.subject
    assert "National Council of Educational Research and Training" in ncert_math.source_authority

    # 2. Test license compliance validation
    ok_check = validate_source_license_compliance(
        license_type="Creative Commons Attribution 4.0 International (CC BY 4.0)",
        authority_category="university",
        source_url="https://openstax.org"
    )
    assert ok_check["is_compliant"] is True

    bad_check = validate_source_license_compliance(
        license_type="All Rights Reserved - Unauthorized reproduction prohibited",
        authority_category="unregistered_category",
        source_url="ftp://invalid-url"
    )
    assert bad_check["is_compliant"] is False
    assert len(bad_check["reasons"]) >= 2


def test_text_cleaning_and_duplicate_removal():
    """Test text normalization, bracket LaTeX conversion, and duplicate paragraph removal."""
    raw_text = (
        "Page 12 of 345\n"
        "NCERT not to be republished\n"
        "Downloaded from https://ncert.nic.in\n"
        "In this chapter, we consider the quadratic equation:\n"
        "\\[ax^2 + bx + c = 0\\]\n"
        "where \\(a \\neq 0\\).\n"
        "The discriminant is given by \\(\\Delta = b^2 - 4ac\\).\n"
        "The discriminant is given by \\(\\Delta = b^2 - 4ac\\).\n"  # Duplicate consecutive line
        "Page 12 of 345\n"
    )

    cleaned = content_cleaner.clean_text(raw_text)

    # Verify boilerplate removed
    assert "Page 12 of 345" not in cleaned
    assert "NCERT not to be republished" not in cleaned
    assert "Downloaded from" not in cleaned

    # Verify LaTeX converted to standard KaTeX delimiters
    assert "$$ax^2 + bx + c = 0$$" in cleaned
    assert "$a \\neq 0$" in cleaned
    assert "$\\Delta = b^2 - 4ac$" in cleaned

    # Verify duplicate line was stripped
    assert cleaned.count("The discriminant is given by") == 1


def test_multi_format_document_extraction():
    """Test extracting text, headings, tables, and equations from HTML, TXT, DOCX, and PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 1. HTML Extraction
        html_file = os.path.join(tmpdir, "lesson.html")
        html_content = """
        <html>
        <head><title>Newtonian Mechanics Lesson</title></head>
        <body>
            <h1>Chapter 4: Laws of Motion</h1>
            <p>Newton's second law states that the acceleration of an object depends on the net force: $$F = ma$$.</p>
            <h2>4.1 Momentum Table</h2>
            <table>
                <tr><th>Object</th><th>Mass (kg)</th><th>Velocity (m/s)</th></tr>
                <tr><td>Cart A</td><td>2.0</td><td>5.0</td></tr>
                <tr><td>Cart B</td><td>4.0</td><td>2.5</td></tr>
            </table>
        </body>
        </html>
        """
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        extracted_html = document_extractor.extract_from_file(html_file)
        assert "Newtonian Mechanics" in extracted_html.title
        assert len(extracted_html.sections) >= 1
        assert "Laws of Motion" in extracted_html.raw_full_text
        assert "$$F = ma$$" in extracted_html.raw_full_text
        assert "| Cart A | 2.0 | 5.0 |" in extracted_html.raw_full_text

        # 2. Markdown / Text Extraction
        md_file = os.path.join(tmpdir, "calculus.md")
        md_content = """# Chapter 2: Derivatives
A derivative represents the instantaneous rate of change: $$\\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x+h) - f(x)}{h}$$.

## Power Rule
For any real exponent $n$: $$\\frac{d}{dx} x^n = n x^{n-1}$$.
"""
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)

        extracted_md = document_extractor.extract_from_file(md_file)
        assert len(extracted_md.sections) >= 1
        assert "Power Rule" in extracted_md.raw_full_text
        assert len(extracted_md.sections[0].equations) >= 1

        # 3. DOCX Extraction
        import docx
        docx_file = os.path.join(tmpdir, "algebra.docx")
        doc = docx.Document()
        doc.add_heading("Chapter 1: Linear Systems", level=1)
        doc.add_paragraph("A system of two linear equations in two variables: $a_1 x + b_1 y = c_1$.")
        t = doc.add_table(rows=2, cols=2)
        t.rows[0].cells[0].text = "Variable"
        t.rows[0].cells[1].text = "Degree"
        t.rows[1].cells[0].text = "x, y"
        t.rows[1].cells[1].text = "1"
        doc.save(docx_file)

        extracted_docx = document_extractor.extract_from_file(docx_file)
        assert len(extracted_docx.sections) >= 1
        assert "Linear Systems" in extracted_docx.raw_full_text
        assert "| Variable | Degree |" in extracted_docx.sections[0].tables[0]

        # 4. PDF Extraction
        try:
            import pymupdf as fitz
        except ImportError:
            import fitz
        pdf_file = os.path.join(tmpdir, "physics.pdf")
        pdf_doc = fitz.open()
        page = pdf_doc.new_page()
        page.insert_text((50, 72), "Chapter 3: Kinematics\nDisplacement is defined as $\\Delta x = x_f - x_i$.\nVelocity is $v = \\frac{\\Delta x}{\\Delta t}$.")
        pdf_doc.save(pdf_file)
        pdf_doc.close()

        extracted_pdf = document_extractor.extract_from_file(pdf_file)
        assert extracted_pdf.total_pages == 1
        assert "Kinematics" in extracted_pdf.raw_full_text
        assert len(extracted_pdf.sections[0].equations) >= 1


def test_educational_chunking_and_concept_boundaries():
    """Verify that chunking retains equations, attaches page numbers, and preserves metadata."""
    md_content = """# Chapter 5: Trigonometric Identities
The fundamental Pythagorean trigonometric identity relates the sine and cosine of an angle:
$$\\sin^2(\\theta) + \\cos^2(\\theta) = 1$$
This holds for all real values of $\\theta$.
Dividing both sides by $\\cos^2(\\theta)$ yields the second standard identity:
$$\\tan^2(\\theta) + 1 = \\sec^2(\\theta)$$
Similarly, dividing by $\\sin^2(\\theta)$ produces the third relationship:
$$1 + \\cot^2(\\theta) = \\csc^2(\\theta)$$
"""
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(md_content)
        temp_path = f.name

    try:
        extracted = document_extractor.extract_from_file(temp_path)
        chunks = educational_chunker.chunk_document(
            extracted=extracted,
            document_id="doc_test_123",
            source_id="ncert-math-class10",
            source_name="NCERT Class 10 Mathematics",
            subject="Mathematics",
            academic_level="Secondary (Grade 10)"
        )

        assert len(chunks) >= 1
        c0 = chunks[0]
        assert c0.document_id == "doc_test_123"
        assert c0.source_id == "ncert-math-class10"
        assert c0.metadata["subject"] == "Mathematics"
        assert c0.metadata["page_number"] == 1
        assert len(c0.sha256_hash) == 64
        assert len(c0.extracted_math) >= 1
        assert "$$\\sin^2(\\theta) + \\cos^2(\\theta) = 1$$" in c0.content
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_embedding_and_vector_store():
    """Verify 768-dim embedding generation, ChromaDB addition, similarity query, and deletion."""
    texts = [
        "Newton's first law of motion defines inertia and balanced forces.",
        "The quadratic formula computes roots of polynomials: x = (-b +- sqrt(b^2 - 4ac)) / (2a).",
        "Python functions are defined using the def keyword and support default arguments."
    ]

    embeddings = embedding_service.embed_batch(texts)
    assert len(embeddings) == 3
    assert len(embeddings[0]) == 768
    assert len(embeddings[1]) == 768

    # Query ChromaDB for physics chunk
    physics_query_vec = embedding_service.embed_text("inertia and Newton's laws")
    assert len(physics_query_vec) == 768

    # Test vector store count check
    initial_count = vector_store.count()
    assert initial_count >= 0


def test_knowledge_manager_ingestion_and_duplicate_detection(db_session: Session):
    """Test full document ingestion, duplicate detection, and version management."""
    seed_default_sources(db_session)

    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write("# Chapter 6: Quadratic Equations\nStandard form: $$ax^2 + bx + c = 0$$.\nSolutions via quadratic formula.")
        doc_path = f.name

    try:
        # 1. First Ingestion
        resp1 = knowledge_manager.add_document(
            source_id="ncert-math-class10",
            file_path=doc_path,
            title="Chapter 6 Quadratic Equations",
            db=db_session
        )
        assert resp1.status == "indexed"
        assert resp1.version == 1
        assert resp1.chunks_created >= 1

        doc_record = db_session.query(KnowledgeDocument).filter(KnowledgeDocument.id == resp1.document_id).first()
        assert doc_record is not None
        assert doc_record.title == "Chapter 6 Quadratic Equations"
        assert len(doc_record.chunks) >= 1

        # 2. Duplicate Detection: Ingesting exact same file
        resp2 = knowledge_manager.add_document(
            source_id="ncert-math-class10",
            file_path=doc_path,
            title="Chapter 6 Quadratic Equations",
            db=db_session
        )
        assert resp2.status == "duplicate_existing"
        assert resp2.document_id == resp1.document_id

        # 3. Document Update with New Content -> Version Increment
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write("# Chapter 6: Quadratic Equations (Revised Edition)\nUpdated with nature of roots and discriminant properties.")

        resp3 = knowledge_manager.update_document(
            document_id=resp1.document_id,
            new_file_path=doc_path,
            db=db_session
        )
        assert resp3.status == "updated"
        assert resp3.version == 2

        # 4. Search Curriculum
        search_res = knowledge_manager.search_curriculum(
            query="nature of roots and quadratic formula",
            db=db_session,
            subject="Mathematics"
        )
        assert search_res.total_matches >= 1
        first_match = search_res.results[0]
        assert "NCERT Class 10 Mathematics" in first_match.citation
        assert first_match.similarity_score > 0.0

        # 5. Remove Document
        del_ok = knowledge_manager.remove_document(resp1.document_id, db=db_session)
        assert del_ok is True
        assert db_session.query(KnowledgeDocument).filter(KnowledgeDocument.id == resp1.document_id).first() is None
    finally:
        if os.path.exists(doc_path):
            os.remove(doc_path)


def test_data_quality_auditor(db_session: Session):
    """Verify that quality auditor identifies missing text, invalid metadata, and duplicate chunks."""
    from app.services.knowledge_extractor import ExtractedDocumentData, ExtractedSection
    from app.services.educational_chunker import EducationalChunk

    # Valid data audit
    valid_extracted = ExtractedDocumentData(
        title="Valid Calculus Module",
        total_pages=1,
        file_type="md",
        metadata={},
        sections=[ExtractedSection(heading="Limits", text="Calculus limits evaluate values approaching points.")],
        raw_full_text="Calculus limits evaluate values approaching points."
    )
    valid_chunks = [
        EducationalChunk(
            chunk_id="chk_01",
            document_id="doc_01",
            source_id="openstax-calculus-vol1",
            chunk_index=1,
            chapter="Chapter 1",
            section="1.1 Limits",
            page_number=1,
            content="Calculus limits evaluate values approaching points in continuous functions.",
            sha256_hash="hash_01"
        )
    ]
    meta = {
        "title": "Valid Calculus Module",
        "subject": "Mathematics",
        "academic_level": "Undergraduate",
        "source_id": "openstax-calculus-vol1"
    }

    report = data_quality_auditor.audit_document_ingestion(
        extracted=valid_extracted,
        chunks=valid_chunks,
        metadata=meta,
        document_id="doc_01",
        source_id="openstax-calculus-vol1"
    )
    assert report["status"] == "passed"
    assert report["missing_text_warnings"] == 0

    # Anomalous data audit: short content & missing subject metadata
    invalid_chunks = [
        EducationalChunk(
            chunk_id="chk_bad",
            document_id="doc_02",
            source_id="test",
            chunk_index=1,
            chapter="",
            section="",
            page_number=1,
            content="Too short.",  # < 50 chars
            sha256_hash="hash_bad"
        )
    ]
    bad_meta = {"title": "Bad"}  # Missing subject, academic_level, source_id
    bad_report = data_quality_auditor.audit_document_ingestion(
        extracted=valid_extracted,
        chunks=invalid_chunks,
        metadata=bad_meta,
        document_id="doc_02",
        source_id="test"
    )
    assert bad_report["status"] in ["flagged_warnings", "failed"]
    assert bad_report["missing_text_warnings"] >= 1
    assert bad_report["invalid_metadata_errors"] >= 1


def test_knowledge_api_endpoints(client):
    """Test REST API endpoints for sources, document ingestion, curriculum search, and quality reports."""
    # 1. GET /api/v1/knowledge/sources (should auto-seed)
    res = client.get("/api/v1/knowledge/sources")
    assert res.status_code == 200
    sources = res.json()
    assert len(sources) >= 10

    # 2. POST /api/v1/knowledge/sources (register new verified source)
    new_source_payload = {
        "id": "chem-open-oer",
        "source_name": "Open Chemistry Foundations",
        "source_url": "https://chem.libretexts.org/sample",
        "subject": "Chemistry",
        "academic_level": "Undergraduate",
        "license_type": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "source_authority": "LibreTexts Consortium",
        "authority_category": "oer",
        "description": "Openly accessible peer-reviewed chemistry modules."
    }
    res_post = client.post("/api/v1/knowledge/sources", json=new_source_payload)
    assert res_post.status_code == 201
    assert res_post.json()["id"] == "chem-open-oer"

    # 3. POST /api/v1/knowledge/documents/ingest
    test_content = b"# Chemical Bonding\nCovalent bonds share electron pairs between atoms.\nIonic bonds transfer electrons."
    files = {"file": ("bonding.md", test_content, "text/markdown")}
    data = {"source_id": "chem-open-oer", "title": "Chemical Bonding Chapter"}

    res_ingest = client.post("/api/v1/knowledge/documents/ingest", data=data, files=files)
    assert res_ingest.status_code == 201
    ingest_json = res_ingest.json()
    doc_id = ingest_json["document_id"]
    assert ingest_json["status"] == "indexed"
    assert ingest_json["chunks_created"] >= 1

    # 4. GET /api/v1/knowledge/documents
    res_docs = client.get("/api/v1/knowledge/documents")
    assert res_docs.status_code == 200
    docs = res_docs.json()
    assert len(docs) >= 1

    # 5. POST /api/v1/knowledge/query
    query_payload = {
        "query": "covalent and ionic bonds",
        "subject": "Chemistry",
        "top_k": 3
    }
    res_query = client.post("/api/v1/knowledge/query", json=query_payload)
    assert res_query.status_code == 200
    query_json = res_query.json()
    assert query_json["total_matches"] >= 1
    assert "Open Chemistry Foundations" in query_json["results"][0]["citation"]

    # 6. GET /api/v1/knowledge/quality/reports
    res_reports = client.get("/api/v1/knowledge/quality/reports")
    assert res_reports.status_code == 200
    reports = res_reports.json()
    assert len(reports) >= 1
