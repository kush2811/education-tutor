# AI Tutor RESTful API Specification

## 1. Overview & Authentication

The **AI-Powered Multimodal Educational Tutor API** is built using FastAPI with OpenAPI 3.1 specifications. It exposes modular endpoints categorized by functional subsystem.

### Base URL
- **Local Development:** `http://localhost:8000/api/v1`
- **Docker Production:** `http://localhost/api/v1`

### Security Scheme
All protected endpoints require an `Authorization` header containing an HMAC-SHA256 Bearer Token:
```http
Authorization: Bearer <JWT_TOKEN>
```
Standard tokens include a 7-day expiration window, student subject permissions, and user ID `sub` claims.

---

## 2. API Endpoint Catalog

### 2.1 Authentication (`/auth`)

#### `POST /auth/register`
Creates a new student profile with hashed credentials.
- **Request Body (`application/json`):**
  ```json
  {
    "email": "student@example.edu",
    "password": "SecurePassword123!",
    "full_name": "Jane Doe",
    "grade_level": "Grade 11 STEM"
  }
  ```
- **Response (`201 Created`):**
  ```json
  {
    "id": "usr_9f48c50",
    "email": "student@example.edu",
    "full_name": "Jane Doe",
    "grade_level": "Grade 11 STEM",
    "is_active": true,
    "created_at": "2026-11-09T10:00:00Z"
  }
  ```

#### `POST /auth/login`
Authenticates credentials and returns an access token.
- **Request Body:** `{"email": "student@example.edu", "password": "SecurePassword123!"}`
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5c...",
    "token_type": "bearer",
    "user": { "id": "usr_9f48c50", "email": "student@example.edu", "full_name": "Jane Doe" }
  }
  ```

#### `GET /auth/me`
Fetches the currently authenticated student profile.
- **Headers:** `Authorization: Bearer <TOKEN>`
- **Response (`200 OK`):** `UserResponse`

---

### 2.2 Student Profiles & Preferences (`/users`)

#### `GET /users/profile`
Retrieves student profile, study preferences, and aggregate learning statistics.

#### `PUT /users/preferences`
Updates student-specific pedagogical and voice synthesis defaults.
- **Request Body:**
  ```json
  {
    "preferred_explanation_level": "intermediate",
    "preferred_voice": "en-US-AriaNeural",
    "preferred_playback_speed": 1.0,
    "preferred_language": "en",
    "preferred_subjects": ["Mathematics", "Physics", "Computer Science"]
  }
  ```

---

### 2.3 Conversation Sessions & History (`/sessions`)

#### `POST /sessions`
Initializes a new persistent tutoring session thread.
- **Request Body:**
  ```json
  {
    "title": "Kinematics & Newton's Laws",
    "subject": "Physics"
  }
  ```

#### `GET /sessions`
Lists all active and archived conversation sessions belonging to the authenticated student.

#### `GET /sessions/{session_id}`
Retrieves full conversation history, stored user turns, AI explanations, formulas, citations, and audio URLs.

#### `DELETE /sessions/{session_id}`
Soft-deletes a conversation thread and its associated message records.

---

### 2.4 Multimodal Ingestion Pipeline (`/pipeline`, `/ingest`)

#### `POST /pipeline/execute`
Executes full multi-step educational problem-solving from raw text input.
- **Request Body:**
  ```json
  {
    "query": "Solve for x: x^2 - 5*x + 6 = 0",
    "session_id": "sess_10a2",
    "subject": "Mathematics",
    "level": "intermediate",
    "synthesize_voice": true
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "session_id": "sess_10a2",
    "input_type": "text",
    "extracted_question": "Solve for x: x^2 - 5*x + 6 = 0",
    "detected_math": ["x^2 - 5*x + 6 = 0"],
    "response_text": "### Problem Understanding\nWe are asked to solve...",
    "sympy_verified": true,
    "final_answer": "x = 2, 3",
    "citations": [],
    "audio_url": "/api/v1/voice/audio/9f48c.mp3",
    "sentence_segments": [ ... ]
  }
  ```

#### `POST /pipeline/execute-file`
Accepts multipart file uploads (`image/png`, `application/pdf`, `audio/wav`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`).
- **Form Data:**
  - `file`: Uploaded file binary
  - `session_id`: Session UUID string
  - `subject`: Academic discipline
  - `synthesize_voice`: Boolean flag

---

### 2.5 Hybrid RAG & Knowledge Base (`/rag`, `/knowledge`)

#### `POST /rag/query`
Executes dual dense ChromaDB + sparse BM25 retrieval with Reciprocal Rank Fusion (RRF).
- **Request Body:**
  ```json
  {
    "query": "Explain Newton's second law and the formula F=ma",
    "subject": "Physics",
    "top_k": 3
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "query": "Explain Newton's second law and the formula F=ma",
    "retrieved_chunks_count": 3,
    "citations": [
      {
        "source_name": "NCERT Class 11 Physics Chapter 5 Laws of Motion",
        "chapter": "Laws of Motion",
        "section": "5.3 Second Law of Motion",
        "page_number": 93,
        "source_url": "https://ncert.nic.in/textbook/pdf/keph105.pdf"
      }
    ],
    "context_text": "..."
  }
  ```

---

### 2.6 Socratic Tutor & Educational Solver (`/tutor`)

#### `POST /tutor/solve`
Generates step-by-step Socratic solution with SymPy symbolic verification.
- **Request Body:**
  ```json
  {
    "query": "Find the derivative of f(x) = 3*x^3 - 5*x + 2",
    "subject": "Mathematics",
    "level": "intermediate"
  }
  ```

#### `POST /tutor/chat`
Handles multi-turn conversational follow-up questions within an existing session context.

#### `POST /tutor/practice`
Generates customized educational practice questions, multiple-choice questions (MCQs), and step-by-step rubrics.

#### `POST /tutor/study-aid`
Generates flashcards, summary sheets, formula cheat sheets, or concept review notes.

---

### 2.7 Validation & Hallucination Guard (`/validation`)

#### `POST /validation/verify`
Validates generated responses against retrieved context chunks and symbolic solvers.
- **Request Body:**
  ```json
  {
    "question": "What is the speed of light?",
    "generated_answer": "The speed of light in vacuum is approximately 3 * 10^8 m/s.",
    "retrieved_context": "The speed of light in vacuum, c, is 299,792,458 m/s (~3x10^8 m/s).",
    "citations": ["NCERT Physics Chapter 1"]
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "is_valid": true,
    "grounding_score": 0.94,
    "citations_verified": true,
    "hallucination_detected": false,
    "mathematical_consistency": true,
    "warnings": []
  }
  ```

---

### 2.8 Neural Voice & Subtitles (`/voice`)

#### `POST /voice/generate`
Synthesizes speech and computes word-level and sentence-level timestamp alignment.
- **Request Body:**
  ```json
  {
    "text": "The derivative is 9 times x squared minus 5.",
    "voice": "en-US-AriaNeural",
    "rate": "+0%"
  }
  ```
- **Response (`200 OK`):**
  ```json
  {
    "audio_url": "/api/v1/voice/audio/a1b2c3.mp3",
    "audio_format": "mp3",
    "duration_seconds": 3.42,
    "voice_used": "en-US-AriaNeural",
    "sentence_segments": [
      {
        "sentence_index": 0,
        "raw_text": "The derivative is 9 times x squared minus 5.",
        "spoken_text": "The derivative is 9 times x squared minus 5.",
        "start_time": 0.0,
        "end_time": 3.42,
        "words": [
          { "word": "The", "start_time": 0.0, "end_time": 0.25 },
          { "word": "derivative", "start_time": 0.25, "end_time": 0.85 }
        ]
      }
    ]
  }
  ```

---

### 2.9 System Health (`/health`)

#### `GET /health`
Verifies database connectivity, vector index readiness, and background workers.
- **Response (`200 OK`):**
  ```json
  {
    "status": "healthy",
    "environment": "production",
    "version": "1.0.0",
    "database": "connected",
    "vector_store": "ready",
    "timestamp": "2026-11-09T10:00:00Z"
  }
  ```
