"""Comprehensive test suite for Phase 8: Text-to-Speech and Synchronized Subtitles."""

import pytest
import os
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.voice import TTSVoiceRequest, NormalizeSpeechRequest
from app.services.speech_normalizer import speech_normalizer
from app.services.voice_service import voice_service, STORAGE_AUDIO_DIR


def test_speech_normalization_math_formulas():
    """Verify that complex mathematical LaTeX formulas are transformed into fluid spoken English."""
    # 1. Newton's second law
    math_text = "The governing formula is $$F = ma$$ where force equals mass times acceleration."
    spoken = speech_normalizer.normalize_structured_text(math_text)
    assert "F equals m times a" in spoken
    assert "$$" not in spoken

    # 2. Fractions, Powers, and Roots
    math_calc = r"The kinetic energy formula is $$K = \frac{1}{2} m v^2$$ and the hypotenuse is $$\sqrt{a^2 + b^2}$$."
    spoken_calc = speech_normalizer.normalize_structured_text(math_calc)
    assert "1 over 2" in spoken_calc
    assert "v squared" in spoken_calc
    assert "square root of" in spoken_calc
    assert r"\frac" not in spoken_calc
    assert r"\sqrt" not in spoken_calc

    # 3. Calculus: Integrals, Derivatives, Limits, and Greek letters
    math_advanced = r"Consider the limit $$\lim_{x \to 0} \frac{\sin(\theta)}{\theta} = 1$$ and the integral $$\int_{0}^{\pi} \sin(x) dx$$."
    spoken_adv = speech_normalizer.normalize_structured_text(math_advanced)
    assert "limit as x approaches 0" in spoken_adv
    assert "theta" in spoken_adv
    assert "integral from 0 to pi" in spoken_adv
    assert r"\lim" not in spoken_adv


def test_speech_normalization_code_blocks():
    """Verify that programming code blocks are summarized rather than reciting raw syntax characters."""
    code_markdown = (
        "Here is the algorithm:\n"
        "```python\n"
        "def binary_search(arr, target):\n"
        "    low, high = 0, len(arr) - 1\n"
        "    while low <= high:\n"
        "        mid = (low + high) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "    return -1\n"
        "```\n"
        "This runs in logarithmic time."
    )

    spoken = speech_normalizer.normalize_structured_text(code_markdown)
    assert "defining the function binary search" in spoken
    assert "logarithmic time" in spoken
    # Ensure raw syntax wasn't read literally
    assert "def binary_search" not in spoken
    assert "len(arr)" not in spoken
    assert "```" not in spoken


def test_speech_normalization_tables_and_citations():
    """Verify that markdown tables and footnote citations are converted into natural speech."""
    table_markdown = (
        "| Quantity | Symbol | Unit |\n"
        "|---|---|---|\n"
        "| Force | F | Newton |\n"
        "| Energy | E | Joule |\n"
        "\n"
        "This is confirmed by textbook physics [1] and standard reference [2]."
    )

    spoken = speech_normalizer.normalize_structured_text(table_markdown)
    assert "Row 1:" in spoken
    assert "Quantity is Force" in spoken
    assert "Symbol is F" in spoken
    assert "Unit is Newton" in spoken
    # Citations like [1] and [2] must be stripped
    assert "[1]" not in spoken
    assert "[2]" not in spoken
    assert "|" not in spoken


def test_sentence_segment_pairing():
    """Verify that split_into_sentence_pairs cleanly correlates display sentences with spoken sentences."""
    markdown_doc = (
        "# 🎓 Newton's Laws\n"
        "Newton's First Law describes inertia.\n"
        "The Second Law states that $$F = ma$$.\n"
        "Every action has an equal and opposite reaction."
    )

    pairs = speech_normalizer.split_into_sentence_pairs(markdown_doc)
    assert len(pairs) >= 3
    # Check that first pair has display text and spoken text
    disp0, spoken0 = pairs[0]
    assert "Newton's" in disp0
    assert "Newton's" in spoken0

    # Check formula sentence
    formula_pair = next((d, s) for d, s in pairs if "$$F = ma$$" in d)
    assert "F equals m times a" in formula_pair[1]


@pytest.mark.asyncio
async def test_voice_service_synthesis_and_timestamps():
    """Verify that voice_service produces timestamped sentence segments and proportional word segments."""
    request = TTSVoiceRequest(
        text="Newton formulated three fundamental laws of motion. The second law defines force as mass times acceleration.",
        voice="en-US-AriaNeural",
        include_word_segments=True
    )

    res = await voice_service.generate_speech_and_subtitles(request)

    assert res.complete_answer_text == request.text
    assert res.duration_seconds > 0.0
    assert len(res.sentence_segments) >= 2

    # Check timestamp integrity
    for i, seg in enumerate(res.sentence_segments):
        assert seg.start_time >= 0.0
        assert seg.end_time > seg.start_time
        assert seg.display_text != ""
        assert seg.spoken_text != ""
        assert len(seg.words) > 0

        # Check word timestamps are bounded within sentence
        for w in seg.words:
            assert w.start_time >= seg.start_time
            assert w.end_time <= seg.end_time + 0.01
            assert w.end_time >= w.start_time

        # Check sequential progression across sentences
        if i > 0:
            prev_seg = res.sentence_segments[i - 1]
            assert seg.start_time >= prev_seg.start_time


def test_voice_service_offline_fallback():
    """Verify that forced-alignment fallback triggers cleanly when cloud synthesis is unavailable."""
    sentence_pairs = [
        ("First sentence.", "First sentence."),
        ("Second sentence.", "Second sentence.")
    ]
    req = TTSVoiceRequest(text="First sentence. Second sentence.")

    res = voice_service._generate_fallback_alignment(
        request=req,
        full_spoken_script="First sentence. Second sentence.",
        sentence_pairs=sentence_pairs,
        error_msg="Connection timed out"
    )

    assert res.alignment_method == "forced_alignment_fallback"
    assert res.audio_format == "browser_speech"
    assert res.duration_seconds > 0.0
    assert len(res.sentence_segments) == 2
    assert res.sentence_segments[0].start_time == 0.0
    assert res.sentence_segments[0].end_time > 0.0


def test_voice_api_endpoints():
    """Verify FastAPI voice endpoints via TestClient."""
    client = TestClient(app)

    # 1. POST /api/v1/voice/normalize
    norm_res = client.post(
        "/api/v1/voice/normalize",
        json={"text": "The energy is $$E = mc^2$$. This is Einstein's mass-energy equivalence."}
    )
    assert norm_res.status_code == 200
    norm_data = norm_res.json()
    assert "E equals m times c squared" in norm_data["spoken_script"]
    assert len(norm_data["sentence_pairs"]) >= 1

    # 2. POST /api/v1/voice/generate
    gen_res = client.post(
        "/api/v1/voice/generate",
        json={
            "text": "Photosynthesis is the process by which green plants create glucose.",
            "voice": "en-US-AriaNeural"
        }
    )
    assert gen_res.status_code == 200
    gen_data = gen_res.json()
    assert gen_data["duration_seconds"] > 0
    assert len(gen_data["sentence_segments"]) >= 1

    # 3. GET /api/v1/voice/audio/{filename} security checks
    # Directory traversal attempt
    bad_res1 = client.get("/api/v1/voice/audio/../../etc/passwd")
    assert bad_res1.status_code in (400, 404)

    # Nonexistent hash
    bad_res2 = client.get("/api/v1/voice/audio/00000000000000000000000000000000.mp3")
    assert bad_res2.status_code == 404
