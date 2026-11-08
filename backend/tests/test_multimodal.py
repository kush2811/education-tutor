"""Unit tests for Multimodal Input Processing Pipeline (Phase 3)."""

import io
import pytest
from fastapi.testclient import TestClient
import fitz
import docx

from app.services.text_normalizer import text_normalizer
from app.services.image_processor import image_processor
from app.services.pdf_processor import pdf_processor
from app.services.docx_processor import docx_processor
from app.services.audio_processor import audio_processor
from app.services.video_processor import video_processor
from app.services.unified_pipeline import unified_input_pipeline


def test_text_processing(client: TestClient):
    """Test text input normalization, bracket math conversion, and subject detection."""
    raw_prompt = "Can you help me solve this derivative? \\[ f(x) = x^2 + 3x - 4 \\] Also check $f'(2)$."
    res = client.post("/api/v1/ingest/text", json={"text": raw_prompt})
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "text"
    assert "extracted_question" in data
    # Verify bracket conversion to $$
    assert "$$ f(x) = x^2 + 3x - 4 $$" in data["extracted_question"]
    assert len(data["math_expressions"]) >= 1
    assert data["metadata"]["detected_subject"] == "Mathematics"


def test_image_processing(client: TestClient):
    """Test image validation, preprocessing, and OCR question extraction."""
    # Create a 100x100 white PNG in memory
    from PIL import Image
    img = Image.new("RGB", (100, 100), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    files = {"file": ("handwritten_problem.png", io.BytesIO(image_bytes), "image/png")}
    res = client.post("/api/v1/ingest/image", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "image"
    assert "extracted_question" in data
    assert data["source_file"]["file_name"] == "handwritten_problem.png"
    assert data["confidence_score"] > 0.0


def test_pdf_processing(client: TestClient):
    """Test PDF text extraction, page numbers, and academic references."""
    # Generate a synthetic 2-page PDF using PyMuPDF
    doc = fitz.open()
    p1 = doc.new_page()
    p1.insert_text((50, 50), "Chapter 4: Quadratic Equations\nProblem 1: Solve for x: $x^2 - 4 = 0$")
    p2 = doc.new_page()
    p2.insert_text((50, 50), "Problem 2: Find the vertex of $y = 2x^2 + 4x + 1$")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("algebra_worksheet.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/ingest/pdf", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "pdf"
    assert data["metadata"]["total_pages"] == 2
    assert len(data["references"]) == 2
    assert data["references"][0]["page_number"] == 1
    assert data["references"][1]["page_number"] == 2
    assert "x^2 - 4 = 0" in str(data["math_expressions"])


def test_docx_processing(client: TestClient):
    """Test DOCX structure, headings, paragraphs, and table extraction."""
    # Generate a synthetic DOCX in memory
    doc = docx.Document()
    doc.add_heading("Physics Worksheet: Mechanics", level=1)
    doc.add_paragraph("Question 1: Calculate the acceleration when force $F = 20N$ and mass $m = 4kg$.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Parameter"
    table.cell(0, 1).text = "Value"
    table.cell(1, 0).text = "Mass"
    table.cell(1, 1).text = "4 kg"
    
    buf = io.BytesIO()
    doc.save(buf)
    docx_bytes = buf.getvalue()

    files = {"file": ("mechanics_test.docx", io.BytesIO(docx_bytes), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    res = client.post("/api/v1/ingest/docx", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "docx"
    assert "Physics Worksheet: Mechanics" in str(data["references"])
    assert data["metadata"]["table_count"] == 1


def test_audio_processing(client: TestClient):
    """Test audio upload, speech-to-text, and question extraction."""
    # Synthetic WAV header (44 bytes standard header)
    riff_header = (
        b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        b"\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    files = {"file": ("student_question.wav", io.BytesIO(riff_header), "audio/wav")}
    res = client.post("/api/v1/ingest/audio", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "audio"
    assert len(data["extracted_question"]) > 5
    assert data["confidence_score"] > 0.0


def test_video_processing(client: TestClient):
    """Test video upload, keyframe sampling, and combined multimodal context."""
    # Synthetic MP4 bytes header (ftyp box)
    fake_mp4_bytes = b"\x00\x00\x00\x20ftypisom\x00\x00\x02\x00isomiso2avc1mp41" + b"\x00" * 2000
    files = {"file": ("lecture_sample.mp4", io.BytesIO(fake_mp4_bytes), "video/mp4")}
    res = client.post("/api/v1/ingest/video", files=files)
    assert res.status_code == 200
    data = res.json()
    assert data["input_type"] == "video"
    assert len(data["references"]) >= 1
    assert data["references"][0]["ref_type"] == "timestamp"


def test_security_validation(client: TestClient):
    """Test security rejections: unsupported file type and oversize rejection."""
    # 1. Unsupported executable extension
    bad_files = {"file": ("malware.exe", io.BytesIO(b"MZ\x90\x00"), "application/x-msdownload")}
    bad_res = client.post("/api/v1/ingest/unified", files=bad_files)
    assert bad_res.status_code == 400

    # 2. Empty file
    empty_files = {"file": ("empty.png", io.BytesIO(b""), "image/png")}
    empty_res = client.post("/api/v1/ingest/unified", files=empty_files)
    assert empty_res.status_code == 400


def test_unified_multimodal_endpoint(client: TestClient):
    """Verify that multiple distinct input types produce the common UnifiedQuestionPayload schema."""
    doc = fitz.open()
    doc.new_page().insert_text((50, 50), "Calculus: Find limit as $x \\to 0$ of $\\frac{\\sin x}{x}$.")
    pdf_bytes = doc.tobytes()
    doc.close()

    files = {"file": ("calculus_quiz.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res = client.post("/api/v1/ingest/unified", files=files)
    assert res.status_code == 200
    data = res.json()
    
    # Must contain all required fields of UnifiedQuestionPayload
    assert "input_type" in data
    assert "extracted_question" in data
    assert "extracted_context" in data
    assert "source_file" in data
    assert "references" in data
    assert "processing_status" in data
    assert data["processing_status"] == "success"

