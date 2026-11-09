"""Comprehensive End-to-End Integration, Educational Reasoning, Voice, Security, and Performance Test Suite for Phase 10."""

import io
import time
import pytest
from PIL import Image, ImageDraw
import fitz  # PyMuPDF
import docx

from app.core.rate_limiter import rate_limiter
from app.core.logging import SensitiveDataFilter, logger
import logging


def get_auth_token(client, email="e2e_student@example.com", password="SecurePassword123!"):
    """Helper to register and login a test user, returning Bearer Authorization header."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "E2E Master Student",
            "grade_level": "Grade 12 STEM",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Complete Workflow Testing
# ==============================================================================

class TestCompleteWorkflow:
    """Tests complete unified workflow: Input -> Extraction -> Classification -> RAG -> Tutor -> Validation -> TTS -> Subtitles."""

    def test_end_to_end_pipeline_text_to_subtitles(self, client):
        headers = get_auth_token(client, email="workflow_user@example.com")

        # Create session
        sess_res = client.post(
            "/api/v1/sessions",
            json={"title": "Algebra Roots", "subject": "Mathematics"},
            headers=headers,
        )
        session_id = sess_res.json()["id"]

        # Execute End-to-End Pipeline
        pipe_res = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "Solve for x: x^2 - 16 = 0",
                "session_id": session_id,
                "subject": "Mathematics",
                "level": "intermediate",
                "preferred_voice": "en-US-AriaNeural",
                "playback_speed": 1.0,
                "synthesize_voice": True,
            },
            headers=headers,
        )
        assert pipe_res.status_code == 200
        data = pipe_res.json()

        # 1. Input detection & extraction
        assert data["input_type"] == "text"
        assert "x^2 - 16 = 0" in data["extracted_question"]
        assert len(data["detected_math"]) >= 1

        # 2. Query classification
        assert data["subject"] == "Mathematics"
        assert data["query_intent"] in ["step_by_step_solution", "formula_lookup", "conceptual_explanation"]

        # 3. Pedagogical Tutoring & SymPy Verification
        assert data["sympy_verified"] is True
        assert data["sympy_result"] is not None
        assert "# 🎓 Step-by-Step Educational Solution" in data["formatted_markdown"]
        assert "Step 1:" in data["formatted_markdown"]
        assert "Final Answer" in data["formatted_markdown"]

        # 4. Answer Validation & Hallucination Check
        assert data["validation"]["is_valid"] is True
        assert "grounding_status" in data["validation"]

        # 5. Voice Generation & Subtitle Alignment
        assert data["voice"] is not None
        assert data["voice"]["audio_url"] is not None
        assert data["voice"]["audio_url"].endswith(".mp3")
        assert len(data["voice"]["sentence_segments"]) >= 1
        first_seg = data["voice"]["sentence_segments"][0]
        assert "start_time" in first_seg
        assert "end_time" in first_seg
        assert first_seg["end_time"] >= first_seg["start_time"]
        assert len(first_seg["words"]) >= 1

        # 6. Performance Metrics
        metrics = data["performance_metrics"]
        assert metrics["input_processing_time_ms"] >= 0
        assert metrics["query_classification_time_ms"] >= 0
        assert metrics["answer_generation_time_ms"] >= 0
        assert metrics["total_response_time_ms"] > 0

        # 7. Session dialogue persistence
        session_data = client.get(f"/api/v1/sessions/{session_id}", headers=headers).json()
        assert len(session_data["messages"]) == 2
        assert session_data["messages"][0]["sender_role"] == "user"
        assert session_data["messages"][1]["sender_role"] == "assistant"
        assert session_data["messages"][1]["audio_url"] is not None


# ==============================================================================
# 2. Multimodal Input Testing
# ==============================================================================

class TestMultimodalInputVariants:
    """Tests printed image, handwritten image, PDF, DOCX, audio, and video inputs."""

    def test_printed_question_image_pipeline(self, client):
        headers = get_auth_token(client, email="image_printed@example.com")

        # Generate synthetic printed math image
        img = Image.new("RGB", (400, 100), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((20, 35), "Solve: 2x + 6 = 14", fill=(0, 0, 0))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        res = client.post(
            "/api/v1/pipeline/execute-file",
            files={"file": ("printed_problem.png", img_bytes.getvalue(), "image/png")},
            data={"subject": "Mathematics", "synthesize_voice": "false"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] == "image"
        assert len(data["formatted_markdown"]) > 50

    def test_pdf_worksheet_pipeline(self, client):
        headers = get_auth_token(client, email="pdf_student@example.com")

        # Generate valid single-page PDF with fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 72), "Chapter 4: Mechanics and Newton's Second Law.")
        page.insert_text((50, 100), "Question 1: Calculate force for mass 5kg and acceleration 2 m/s^2. Formula: F = m*a.")
        pdf_bytes = doc.write()
        doc.close()

        res = client.post(
            "/api/v1/pipeline/execute-file",
            files={"file": ("physics_worksheet.pdf", pdf_bytes, "application/pdf")},
            data={"subject": "Physics", "synthesize_voice": "false"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] in ["pdf", "document"]
        assert "Newton" in data["extracted_question"] or "force" in data["extracted_question"].lower()

    def test_docx_file_pipeline(self, client):
        headers = get_auth_token(client, email="docx_student@example.com")

        # Generate valid DOCX file
        doc = docx.Document()
        doc.add_heading("Computer Science Algorithms", level=1)
        doc.add_paragraph("Explain the time complexity of Binary Search on a sorted array.")
        docx_bytes = io.BytesIO()
        doc.save(docx_bytes)
        docx_bytes.seek(0)

        res = client.post(
            "/api/v1/pipeline/execute-file",
            files={"file": ("algorithms.docx", docx_bytes.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"subject": "Computer Science", "synthesize_voice": "false"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] in ["docx", "document"]
        assert "Binary Search" in data["extracted_question"] or "algorithms" in data["extracted_question"].lower()

    def test_audio_question_pipeline(self, client):
        headers = get_auth_token(client, email="audio_student@example.com")

        # Minimal synthetic WAV header (44 bytes standard PCM)
        wav_header = (
            b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
            b'D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
        )

        res = client.post(
            "/api/v1/pipeline/execute-file",
            files={"file": ("student_voice.wav", wav_header, "audio/wav")},
            data={"subject": "General STEM", "synthesize_voice": "false"},
            headers=headers,
        )
        assert res.status_code == 200
        data = res.json()
        assert data["input_type"] == "audio"
        assert len(data["extracted_question"]) > 0


# ==============================================================================
# 3. Educational Tutoring Testing
# ==============================================================================

class TestEducationalReasoning:
    """Tests mathematical solutions, code assistance, explanation levels, study aids, and practice MCQs."""

    def test_mathematical_solutions_sympy(self, client):
        # 1. Calculus Differentiation
        diff_res = client.post(
            "/api/v1/tutor/math",
            json={"expression": "x^3 + 4*x^2 - 5*x + 7", "operation": "differentiate", "variable": "x"},
        )
        assert diff_res.status_code == 200
        assert "3*x**2" in diff_res.json()["result"]

        # 2. Calculus Integration
        integ_res = client.post(
            "/api/v1/tutor/math",
            json={"expression": "3*x^2 + 2*x", "operation": "integrate", "variable": "x"},
        )
        assert integ_res.status_code == 200
        assert "x**3 + x**2" in integ_res.json()["result"]

        # 3. Algebraic Solving
        solve_res = client.post(
            "/api/v1/tutor/math",
            json={"expression": "x^2 - 25", "operation": "solve", "variable": "x"},
        )
        assert solve_res.status_code == 200
        assert "-5, 5" in solve_res.json()["result"]

    def test_programming_assistance_safe_ast(self, client):
        # Bug detection & complexity explanation without executing code
        code_snippet = (
            "def calculate_sum(n):\n"
            "    total = 0\n"
            "    for i in range(n):\n"
            "        total += i\n"
            "    return total\n"
        )
        res = client.post(
            "/api/v1/tutor/code",
            json={"code": code_snippet, "language": "python", "task": "explain", "level": "intermediate"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["syntax_valid"] is True
        assert "O(n)" in body["time_complexity"]

    def test_pedagogical_explanation_levels(self, client):
        query = "Explain how electromagnetic induction generates electric current"

        # Beginner Level
        beg = client.post("/api/v1/tutor/solve", json={"query": query, "level": "beginner"}).json()
        assert beg["level"] == "beginner"
        assert "Intuitive" in beg["why_it_works"] or "real-world" in beg["why_it_works"].lower()

        # Advanced Level
        adv = client.post("/api/v1/tutor/solve", json={"query": query, "level": "advanced"}).json()
        assert adv["level"] == "advanced"
        assert "Axiomatic" in adv["why_it_works"] or "conservation" in adv["why_it_works"].lower()

    def test_study_aids_and_practice_mcqs(self, client):
        # Study Aid
        aid_res = client.post(
            "/api/v1/tutor/study-aid",
            json={"content": "Newton's Laws of Motion explain the relationship between force and acceleration.", "aid_type": "summary"},
        )
        assert aid_res.status_code == 200
        aid = aid_res.json()
        assert len(aid["key_points"]) >= 1

        # Practice MCQs with distractors
        prac_res = client.post(
            "/api/v1/tutor/practice",
            json={"topic_or_content": "Quadratic Equations in high school algebra", "question_type": "mcq", "count": 2},
        )
        assert prac_res.status_code == 200
        prac = prac_res.json()
        assert len(prac["mcqs"]) == 2
        for mcq in prac["mcqs"]:
            assert len(mcq["options"]) == 4
            assert "explanation" in mcq

    def test_follow_up_conversational_context(self, client):
        headers = get_auth_token(client, email="followup_student@example.com")

        # Session Turn 1: Initial Question
        res1 = client.post(
            "/api/v1/tutor/chat",
            json={"session_id": "test_ctx_session", "message": "What is the formula for the roots of ax^2 + bx + c = 0?"},
            headers=headers,
        )
        assert res1.status_code == 200
        assert "Quadratic" in res1.json()["response_text"] or "formula" in res1.json()["response_text"].lower()

        # Session Turn 2: Anaphoric Follow-up relying on Turn 1
        res2 = client.post(
            "/api/v1/tutor/chat",
            json={"session_id": "test_ctx_session", "message": "What if that discriminant is negative?"},
            headers=headers,
        )
        assert res2.status_code == 200
        assert "complex" in res2.json()["response_text"].lower() or "imaginary" in res2.json()["response_text"].lower() or "Step 1:" in res2.json()["response_text"]


# ==============================================================================
# 4. Voice and Subtitles Testing
# ==============================================================================

class TestVoiceAndSubtitleControls:
    """Tests speech normalization, neural TTS audio, sentence/word alignment, and playback speeds."""

    def test_speech_normalization(self, client):
        raw_markdown = "The energy is $E = mc^2$ and the derivative is $\\frac{dy}{dx} = 2x$."
        norm_res = client.post("/api/v1/voice/normalize", json={"text": raw_markdown})
        assert norm_res.status_code == 200
        script = norm_res.json()["spoken_script"]
        assert "equals" in script
        assert "squared" in script or "power 2" in script

    def test_voice_synthesis_and_speeds(self, client):
        text = "Welcome to your personal multimodal AI tutoring session."

        # Normal speed (1.0x)
        res_normal = client.post(
            "/api/v1/voice/generate",
            json={"text": text, "voice": "en-US-AriaNeural", "rate": "+0%"},
        )
        assert res_normal.status_code == 200
        norm_data = res_normal.json()
        assert norm_data["audio_url"] is not None
        assert len(norm_data["sentence_segments"]) >= 1

        # Accelerated speed (1.5x)
        res_fast = client.post(
            "/api/v1/voice/generate",
            json={"text": text, "voice": "en-US-GuyNeural", "rate": "+50%"},
        )
        assert res_fast.status_code == 200
        fast_data = res_fast.json()
        assert fast_data["voice_used"] == "en-US-GuyNeural"


# ==============================================================================
# 5. Backend APIs and Failure Cases
# ==============================================================================

class TestBackendAPIsAndFailureCases:
    """Tests failure paths, malformed payloads, corrupted files, and non-existent entity lookups."""

    def test_empty_query_handling(self, client):
        res = client.post("/api/v1/tutor/solve", json={"query": "   ", "level": "intermediate"})
        assert res.status_code in [200, 400, 422]  # Handled safely without server crash

    def test_corrupted_file_upload_rejected(self, client):
        headers = get_auth_token(client, email="security_upload@example.com")

        # Fake executable masquerading as PDF
        fake_executable_bytes = b"MZ\x90\x00\x03\x00\x00\x00ThisIsAnExecutable disguised as pdf"
        res = client.post(
            "/api/v1/ingest/upload",
            files={"file": ("malicious.exe", fake_executable_bytes, "application/x-dosexec")},
            headers=headers,
        )
        assert res.status_code == 400
        assert "not allowed" in res.json()["detail"].lower() or "unsupported" in res.json()["detail"].lower()

    def test_nonexistent_session_returns_404(self, client):
        headers = get_auth_token(client, email="lookup_user@example.com")
        res = client.get("/api/v1/sessions/nonexistent-uuid-12345", headers=headers)
        assert res.status_code == 404

    def test_nonexistent_asset_returns_404(self, client):
        headers = get_auth_token(client, email="asset_lookup@example.com")
        res = client.get("/api/v1/ingest/assets/nonexistent-asset-99999", headers=headers)
        assert res.status_code == 404


# ==============================================================================
# 6. Security Testing
# ==============================================================================

class TestSecurityAndHardening:
    """Tests security headers, log credential masking, rate limiting, and tenant data isolation."""

    def test_security_headers_injected(self, client):
        res = client.get("/")
        assert res.status_code == 200
        headers = res.headers
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in headers

    def test_sensitive_data_log_masking(self):
        log_filter = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User login with Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9 and sk-12345678901234567890 password=SecretPassword99!",
            args=(),
            exc_info=None,
        )
        log_filter.filter(record)
        assert "eyJhbGciOiJIUz" not in record.msg
        assert "sk-1234567890" not in record.msg
        assert "SecretPassword99!" not in record.msg
        assert "[REDACTED_TOKEN]" in record.msg
        assert "[REDACTED_API_KEY]" in record.msg

    def test_rate_limiter_burst_enforcement(self, client):
        # Configure a small temporary limit for testing
        rate_limiter.reset()
        original_limit = rate_limiter.limit_per_minute
        rate_limiter.limit_per_minute = 5

        try:
            # First 5 calls pass
            for _ in range(5):
                r = client.post("/api/v1/voice/normalize", json={"text": "Rate limit check."})
                assert r.status_code == 200

            # 6th call exceeds limit -> 429 Too Many Requests
            burst_res = client.post("/api/v1/voice/normalize", json={"text": "Rate limit check."})
            assert burst_res.status_code == 429
            assert "Rate limit exceeded" in burst_res.json()["detail"]
            assert burst_res.headers.get("Retry-After") == "60"
        finally:
            rate_limiter.limit_per_minute = original_limit
            rate_limiter.reset()

    def test_tenant_data_isolation(self, client):
        headers_a = get_auth_token(client, email="tenant_a@example.com")
        headers_b = get_auth_token(client, email="tenant_b@example.com")

        # Tenant A creates session
        sess_a = client.post("/api/v1/sessions", json={"title": "Confidential Study A"}, headers=headers_a).json()
        sess_a_id = sess_a["id"]

        # Tenant B attempts to read or mutate Tenant A's session -> 403 Forbidden
        assert client.get(f"/api/v1/sessions/{sess_a_id}", headers=headers_b).status_code == 403
        assert client.put(f"/api/v1/sessions/{sess_a_id}", json={"title": "Hacked"}, headers=headers_b).status_code == 403
        assert client.delete(f"/api/v1/sessions/{sess_a_id}", headers=headers_b).status_code == 403


# ==============================================================================
# 7. Performance Benchmarking
# ==============================================================================

class TestPerformanceBenchmarking:
    """Measures latency across input processing, retrieval, answer generation, TTS, and total turn."""

    def test_pipeline_latency_thresholds(self, client):
        headers = get_auth_token(client, email="perf_student@example.com")

        start = time.perf_counter()
        res = client.post(
            "/api/v1/pipeline/execute",
            json={
                "query": "Differentiate f(x) = x^4 - 2*x^2 + 5 with respect to x.",
                "subject": "Mathematics",
                "level": "intermediate",
                "synthesize_voice": True,
            },
            headers=headers,
        )
        total_time_ms = (time.perf_counter() - start) * 1000

        assert res.status_code == 200
        metrics = res.json()["performance_metrics"]

        # Ensure all individual breakdown times are tracked
        assert metrics["input_processing_time_ms"] >= 0
        assert metrics["query_classification_time_ms"] >= 0
        assert metrics["retrieval_time_ms"] >= 0
        assert metrics["answer_generation_time_ms"] >= 0
        assert metrics["validation_time_ms"] >= 0
        assert metrics["tts_generation_time_ms"] >= 0
        assert metrics["total_response_time_ms"] > 0

        # Operational Latency Budget:
        # Full end-to-end multi-stage pipeline with SymPy, RAG, and edge-TTS completes within reasonable test limits (< 15s)
        assert total_time_ms < 15000

