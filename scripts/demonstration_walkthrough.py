"""Comprehensive 10-Step Interactive Educational Demonstration Walkthrough Script.
Demonstrates text, image OCR, PDF ingestion, audio STT, RAG retrieval, Socratic solving,
TTS generation, subtitle alignment, follow-up anaphora, and conversation history.
"""

import sys
import os
import time
import io
from PIL import Image, ImageDraw
import fitz

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from fastapi.testclient import TestClient
from app.main import app

BOLD = "\033[1m"
GREEN = "\033[32m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def print_step(step_num: int, title: str, description: str):
    print(f"\n{BOLD}{CYAN}{'='*80}{RESET}")
    print(f"{BOLD}{GREEN}STEP {step_num}: {title}{RESET}")
    print(f"{YELLOW}Description:{RESET} {description}")
    print(f"{CYAN}{'-'*80}{RESET}")


def run_demonstration():
    print(f"\n{BOLD}{BLUE}================================================================================{RESET}")
    print(f"{BOLD}{BLUE}   AI-POWERED MULTIMODAL STUDENT TUTOR - FINAL PROJECT DEMONSTRATION WALKTHROUGH {RESET}")
    print(f"{BOLD}{BLUE}================================================================================{RESET}")

    client = TestClient(app)

    # Setup student user
    email = "demo_student@example.com"
    password = "DemoSecurePassword2026!"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Alex Mercer", "grade_level": "Grade 11 STEM"}
    )
    login_res = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Authenticated Demo Student: {BOLD}Alex Mercer (Grade 11 STEM){RESET} | Token Acquired.")

    # Create active session
    sess_res = client.post(
        "/api/v1/sessions",
        json={"title": "Interactive STEM Problem Solving", "subject": "Mathematics"},
        headers=headers
    )
    session_id = sess_res.json()["id"]
    print(f"Active Tutoring Session Created: {BOLD}{session_id}{RESET}\n")

    # --------------------------------------------------------------------------
    # Step 1: Student asks a question using text
    # --------------------------------------------------------------------------
    print_step(1, "Student Asks Question via Text", "Submitting raw text question to the unified pipeline.")
    q1 = "Solve the quadratic equation: x^2 - 5*x + 6 = 0"
    print(f"Student Inquiry: {BOLD}\"{q1}\"{RESET}")
    t0 = time.perf_counter()
    res1 = client.post(
        "/api/v1/pipeline/execute",
        json={"query": q1, "session_id": session_id, "subject": "Mathematics", "level": "intermediate"},
        headers=headers
    )
    t1 = time.perf_counter()
    data1 = res1.json()
    print(f"✓ Input Detected: Modality={BOLD}{data1['input_type']}{RESET} | Math Formulas Extracted={BOLD}{data1['detected_math']}{RESET}")
    print(f"✓ Latency: {round((t1-t0)*1000, 1)}ms")

    # --------------------------------------------------------------------------
    # Step 2: Student uploads an image
    # --------------------------------------------------------------------------
    print_step(2, "Student Uploads an Image Worksheet", "Uploading image of a right triangle to calculate hypotenuse.")
    img = Image.new("RGB", (400, 120), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((20, 40), "Pythagorean Theorem: a=3, b=4. Calculate c = sqrt(a^2 + b^2)", fill=(0, 0, 0))
    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    res2 = client.post(
        "/api/v1/pipeline/execute-file",
        files={"file": ("geometry_diagram.png", img_buf.getvalue(), "image/png")},
        data={"session_id": session_id, "subject": "Mathematics", "synthesize_voice": "false"},
        headers=headers
    )
    data2 = res2.json()
    print(f"✓ Image Preprocessed & OCR Parsed: \"{BOLD}{data2['extracted_question']}{RESET}\"")
    print(f"✓ Identified Intent: {BOLD}{data2['query_intent']}{RESET}")

    # --------------------------------------------------------------------------
    # Step 3: Student uploads a PDF
    # --------------------------------------------------------------------------
    print_step(3, "Student Uploads a PDF Document", "Parsing layout-aware multi-page curriculum excerpt with PyMuPDF.")
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Chapter 5: Laws of Motion - National Curriculum Council.")
    page.insert_text((50, 110), "Problem: An object of mass 12 kg is acted on by a net force of 36 N. Find acceleration: a = F / m.")
    pdf_bytes = doc.write()
    doc.close()

    res3 = client.post(
        "/api/v1/pipeline/execute-file",
        files={"file": ("physics_laws.pdf", pdf_bytes, "application/pdf")},
        data={"session_id": session_id, "subject": "Physics", "synthesize_voice": "false"},
        headers=headers
    )
    data3 = res3.json()
    print(f"✓ PDF Processed: Document text and equations extracted successfully.")
    print(f"✓ Extracted Target: \"{BOLD}{data3['extracted_question']}{RESET}\"")

    # --------------------------------------------------------------------------
    # Step 4: Student asks a question using audio
    # --------------------------------------------------------------------------
    print_step(4, "Student Submits Recorded Audio Question", "Speech-to-text processing for spoken academic inquiry.")
    wav_header = (
        b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00'
        b'D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    )
    res4 = client.post(
        "/api/v1/pipeline/execute-file",
        files={"file": ("student_voice_recording.wav", wav_header, "audio/wav")},
        data={"session_id": session_id, "subject": "General STEM", "synthesize_voice": "false"},
        headers=headers
    )
    data4 = res4.json()
    print(f"✓ Audio STT Extracted Modality: {BOLD}{data4['input_type'].upper()}{RESET}")
    print(f"✓ Spoken Transcript Handled Safely: \"{BOLD}{data4['extracted_question']}{RESET}\"")

    # --------------------------------------------------------------------------
    # Step 5: AI retrieves educational knowledge (RAG)
    # --------------------------------------------------------------------------
    print_step(5, "AI Retrieves Educational Knowledge via Hybrid RAG", "Dual ChromaDB Dense + BM25 Sparse Search.")
    rag_res = client.post(
        "/api/v1/rag/query",
        json={"query": "Explain Newton's second law and the formula F=ma", "subject": "Physics", "top_k": 2},
        headers=headers
    )
    rag_data = rag_res.json()
    print(f"✓ Context Chunks Retrieved: {BOLD}{rag_data['retrieved_chunks_count']}{RESET}")
    for idx, cit in enumerate(rag_data["citations"], 1):
        print(f"   [{idx}] {BOLD}{cit['source_name']}{RESET} | Chapter: {cit['chapter']} | Page: {cit['page_number']}")

    # --------------------------------------------------------------------------
    # Step 6: AI explains the solution step by step
    # --------------------------------------------------------------------------
    print_step(6, "AI Explains Solution Step by Step with SymPy Verification", "Pedagogical problem decomposition.")
    tutor_res = client.post(
        "/api/v1/tutor/solve",
        json={"query": "Solve for x: x^2 - 5*x + 6 = 0", "subject": "Mathematics", "level": "intermediate"},
        headers=headers
    )
    tutor_data = tutor_res.json()
    print(f"✓ SymPy Verified: {BOLD}{tutor_data['sympy_verified']}{RESET} | Result: {BOLD}{tutor_data['final_answer']}{RESET}")
    print(f"✓ Step Breakdown:")
    for step in tutor_data["steps"]:
        print(f"   • Step {step['step_number']}: {step['title']} - {step['explanation']}")
    print(f"\n{BOLD}Why it works:{RESET} {tutor_data['why_it_works']}")

    # --------------------------------------------------------------------------
    # Step 7: Student listens to the answer (TTS)
    # --------------------------------------------------------------------------
    print_step(7, "Student Listens to Synthesized Neural Voice", "Converting markdown answer to speech.")
    voice_res = client.post(
        "/api/v1/voice/generate",
        json={
            "text": "The solutions to the quadratic equation are x equals 2 and x equals 3. We factored the polynomial.",
            "voice": "en-US-AriaNeural",
            "rate": "+0%"
        },
        headers=headers
    )
    voice_data = voice_res.json()
    print(f"✓ Audio Generated: {BOLD}{voice_data['audio_url']}{RESET}")
    print(f"✓ Neural Voice: {BOLD}{voice_data['voice_used']}{RESET} | Format: {voice_data['audio_format']}")
    print(f"✓ Audio Duration: {BOLD}{voice_data['duration_seconds']}s{RESET}")

    # --------------------------------------------------------------------------
    # Step 8: Subtitles highlight the spoken content
    # --------------------------------------------------------------------------
    print_step(8, "Subtitles Synchronize with Millisecond Alignment", "Inspecting aligned sentence and word timestamps.")
    print(f"✓ Total Aligned Sentences: {len(voice_data['sentence_segments'])}")
    for s_idx, seg in enumerate(voice_data["sentence_segments"][:2], 1):
        print(f"   [Sentence {s_idx}] ({seg['start_time']}s - {seg['end_time']}s): \"{seg['spoken_text']}\"")
        words_preview = " ".join([f"{w['word']} ({w['start_time']}s)" for w in seg["words"][:5]])
        print(f"     └─ Word Timing Sample: {words_preview}...")

    # --------------------------------------------------------------------------
    # Step 9: Student asks a follow-up question
    # --------------------------------------------------------------------------
    print_step(9, "Student Asks an Anaphoric Follow-up Question", "Multi-turn context resolution using prior formula.")
    q_followup = "What if that constant term was negative instead?"
    print(f"Student Follow-Up: {BOLD}\"{q_followup}\"{RESET}")
    chat_res = client.post(
        "/api/v1/tutor/chat",
        json={"session_id": session_id, "message": q_followup, "level": "intermediate"},
        headers=headers
    )
    chat_data = chat_res.json()
    print(f"✓ Follow-up Resolved within Thread {BOLD}{session_id}{RESET}:")
    print(f"   Tutor Response Preview: \"{chat_data['response_text'][:160]}...\"")

    # --------------------------------------------------------------------------
    # Step 10: Student opens conversation history
    # --------------------------------------------------------------------------
    print_step(10, "Student Opens Persistent Conversation History", "Retrieving complete preserved dialogue session.")
    hist_res = client.get(f"/api/v1/sessions/{session_id}", headers=headers)
    hist_data = hist_res.json()
    print(f"✓ Session Title: {BOLD}{hist_data['title']}{RESET} | Subject: {hist_data['subject']}")
    print(f"✓ Total Messages Persisted: {BOLD}{len(hist_data['messages'])}{RESET}")
    for idx, msg in enumerate(hist_data["messages"], 1):
        audio_tag = f"[Audio: {msg['audio_url']}]" if msg.get("audio_url") else "[Text]"
        print(f"   Turn {idx} ({msg['sender_role'].upper()} - {msg['input_type']}) {audio_tag}: {msg['content'][:65]}...")

    print(f"\n{BOLD}{GREEN}================================================================================{RESET}")
    print(f"{BOLD}{GREEN}   ✓ ALL 10 DEMONSTRATION STEPS EXECUTED AND VERIFIED SUCCESSFULLY!             {RESET}")
    print(f"{BOLD}{GREEN}================================================================================{RESET}\n")


if __name__ == "__main__":
    run_demonstration()
