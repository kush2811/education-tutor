# AI-Powered Multimodal Student Tutor & Problem Solver

An intelligent, multi-turn, multimodal tutoring system engineered to guide students through complex STEM problems using the Socratic method, mathematical verification, diagram comprehension, and voice interaction.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    subgraph Client ["Frontend Client (React + TypeScript + Vite)"]
        ChatUI["Socratic Chat Interface"]
        CanvasUI["Interactive Whiteboard / Scratchpad"]
        MathEngine["KaTeX Formula Rendering ($...$)"]
        AuthUI["Student Authentication (JWT)"]
        CurriculumUI["Verified OER Curriculum Explorer"]
        UploadUI["Multimodal File Uploader (Images/PDFs)"]
    end

    subgraph API_Gateway ["FastAPI Backend Services"]
        Router["API v1 Gateway (/api/v1)"]
        AuthModule["Auth & Security Service (PBKDF2/JWT)"]
        SessionMgr["Session & Conversation Manager"]
        IngestRouter["File Upload & Ingestion Gateway"]
    end

    subgraph Modular_Services ["Modular AI & Tutoring Services"]
        AIGateway["AI Gateway (Gemini 1.5 Multimodal)"]
        SocraticEngine["Socratic Pedagogical State Machine"]
        SymPyVerifier["SymPy Symbolic Math Verifier"]
        VisionOCR["Multimodal Vision & Diagram OCR"]
        DocParser["Layout-Aware Document Parser (PyMuPDF)"]
        RAGEngine["Hybrid RAG Engine (Dense + BM25)"]
        KnowledgeBase["OER Curriculum Manager"]
        VoiceService["Voice & Speech Service"]
        SubtitleAligner["Word Timestamp Alignment Engine"]
    end

    subgraph Persistence ["Data & Vector Storage"]
        SQLiteDB[("SQLite Database (Async/Sync SQLAlchemy)")]
        VectorStore[("ChromaDB Vector Store (Curriculum RAG)")]
        AssetStorage[("Uploaded Images, Documents & Audio")]
    end

    Client -->|HTTP / WebSocket| Router
    Router --> AuthModule
    Router --> SessionMgr
    Router --> IngestRouter
    Router --> Modular_Services
    SessionMgr --> SQLiteDB
    AuthModule --> SQLiteDB
    IngestRouter --> AssetStorage
    IngestRouter --> SQLiteDB
    Modular_Services --> SQLiteDB
    Modular_Services --> VectorStore
```

---

## 📁 Project Directory Structure

```text
ai-multimodal-tutor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── auth.py          # Student registration, login, /me JWT verification
│   │   │       │   ├── user.py          # Student profile management & dashboard analytics
│   │   │       │   ├── health.py        # System health & DB readiness endpoint
│   │   │       │   ├── session.py       # Tutoring session & message CRUD (Conversations)
│   │   │       │   ├── ingest.py        # Multimodal ingestion: text, images, PDF, DOCX, audio, video
│   │   │       │   ├── knowledge.py     # Educational sources registry, doc ingestion & curriculum search
│   │   │       │   └── rag.py           # End-to-end RAG question answering, retrieval diagnostics & evaluation
│   │   │       └── router.py            # Aggregated v1 API router
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings & environment config
│   │   │   ├── file_security.py         # MIME validation, size limits & sanitization
│   │   │   ├── logging.py               # Structured application logger
│   │   │   └── security.py              # PBKDF2 password hashing & HMAC-SHA256 JWT
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy declarative base
│   │   │   └── session.py               # Synchronous SQLite session provider
│   │   ├── models/
│   │   │   ├── user.py                  # User / Student profile ORM model
│   │   │   ├── session.py               # StudySession & SessionMessage ORM models
│   │   │   ├── asset.py                 # UploadedAsset ORM model
│   │   │   └── knowledge.py             # EducationalSource, KnowledgeDocument, DocumentChunk, QualityReport
│   │   ├── schemas/
│   │   │   ├── health.py                # Health check response schemas
│   │   │   ├── auth.py                  # Login, registration, token schemas
│   │   │   ├── user.py                  # User profile schemas
│   │   │   ├── session.py               # Session & Message request/response schemas
│   │   │   ├── asset.py                 # Uploaded file schemas
│   │   │   ├── unified_input.py         # UnifiedQuestionPayload, SourceFileInfo & schemas
│   │   │   ├── knowledge.py             # Sources, chunks, documents, queries & quality audit schemas
│   │   │   └── rag.py                   # RAG queries, responses, citations, diagnostics & evaluation schemas
│   │   ├── services/
│   │   │   ├── text_normalizer.py       # Whitespace & LaTeX bracket normalization
│   │   │   ├── image_processor.py       # Image preprocessing & Gemini vision OCR
│   │   │   ├── pdf_processor.py         # PyMuPDF page-aware extraction & table parser
│   │   │   ├── docx_processor.py        # python-docx structured hierarchy parser
│   │   │   ├── audio_processor.py       # Audio STT with Gemini & offline fallback
│   │   │   ├── video_processor.py       # 30s keyframe sampling & multimodal audio/visual fusion
│   │   │   ├── unified_pipeline.py      # Master input router to UnifiedQuestionPayload
│   │   │   ├── knowledge_sources.py     # Source registry & legal compliance validation
│   │   │   ├── knowledge_cleaner.py     # Text cleaning, boilerplate & duplicate removal
│   │   │   ├── knowledge_extractor.py   # Multi-format doc extractor (PDF, DOCX, HTML, TXT)
│   │   │   ├── educational_chunker.py   # Concept-aware semantic chunking with formula retention
│   │   │   ├── embedding_service.py     # Gemini text-embedding-004 + 768-dim local projection
│   │   │   ├── vector_store.py          # Persistent ChromaDB vector store collection manager
│   │   │   ├── data_quality.py          # Validation auditing for missing text & duplicate chunks
│   │   │   ├── knowledge_manager.py     # Knowledge lifecycle, duplicate detection, versioning
│   │   │   ├── query_processor.py       # Query normalization, domain classification, and expansion
│   │   │   ├── rag_retriever.py         # Hybrid retrieval (ChromaDB Dense + BM25 Sparse) & RRF reranking
│   │   │   ├── context_builder.py       # Reference cards and citation metadata mapping
│   │   │   ├── answer_generator.py      # Grounded LLM answering with anti-hallucination guardrails
│   │   │   ├── rag_service.py           # Master 5-stage RAG coordinator & latency tracker
│   │   │   └── rag_evaluator.py         # Benchmark evaluator measuring recall@k, precision, and latency
│   │   └── main.py                      # FastAPI app factory, CORS & lifespan
│   ├── tests/
│   │   ├── conftest.py                  # Pytest fixtures & test client
│   │   ├── test_api.py                  # Health, Auth, Session & Upload test suite
│   │   ├── test_multimodal.py           # Comprehensive multimodal ingestion test suite
│   │   ├── test_knowledge_base.py       # Phase 4 educational knowledge base test suite
│   │   └── test_rag.py                  # Phase 5 RAG pipeline & evaluation test suite
│   ├── requirements.txt                 # Backend Python dependencies
│   ├── pytest.ini                       # Pytest test runner config
│   └── .env.example                     # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AuthModal.tsx            # Student sign in & account registration
│   │   │   ├── ChatInterface.tsx        # Multi-turn chat with LaTeX math rendering
│   │   │   ├── CurriculumView.tsx       # Verified OER curriculum explorer
│   │   │   ├── FileUploadModal.tsx      # Image, PDF & worksheet uploader
│   │   │   ├── Header.tsx               # App header with live backend status & auth
│   │   │   ├── MathRenderer.tsx         # KaTeX formula renderer for $...$ and $$...$$
│   │   │   ├── ProfileModal.tsx         # User profile and learning progress
│   │   │   ├── SessionList.tsx          # Study sessions sidebar with creation modal
│   │   │   ├── TutorResponse.tsx        # Socratic markdown answer display with KaTeX & code
│   │   │   ├── VoicePlayer.tsx          # Audio playback dock with sentence highlighting
│   │   │   └── WhiteboardCanvas.tsx     # Interactive student scratchpad & canvas
│   │   ├── pages/
│   │   │   ├── LandingPage.tsx          # Landing page with feature highlights & hero
│   │   │   ├── LoginPage.tsx            # Full-page login interface
│   │   │   ├── RegisterPage.tsx         # Registration interface with grade/subject selection
│   │   │   └── StudentDashboard.tsx     # Student dashboard with metrics & active sessions
│   │   ├── services/
│   │   │   └── api.ts                   # Type-safe API client (Auth, Sessions, Uploads)
│   │   ├── types/
│   │   │   └── index.ts                 # Shared TypeScript interfaces
│   │   ├── App.tsx                      # Main application view & tab coordinator
│   │   ├── index.css                    # Tailwind CSS base & utilities
│   │   ├── vite-env.d.ts                # Vite environment typings
│   │   └── main.tsx                     # React DOM entrypoint
│   ├── package.json                     # Frontend npm packages
│   ├── vite.config.ts                   # Vite bundler configuration
│   ├── tsconfig.json                    # TypeScript compiler options
│   ├── tailwind.config.js               # Tailwind styling configuration
│   └── .env.example                     # Frontend environment template
├── scripts/
│   ├── run_backend.ps1                  # PowerShell script to start FastAPI backend
│   └── run_frontend.ps1                 # PowerShell script to start Vite frontend
├── .env.example                         # Master environment variables template
├── .gitignore                           # Git ignore rules for Python, Node, DB & secrets
└── README.md                            # Comprehensive technical documentation
├── scripts/
│   ├── run_backend.ps1                  # PowerShell script to start FastAPI backend
│   └── run_frontend.ps1                 # PowerShell script to start Vite frontend
├── .env.example                         # Master environment variables template
├── .gitignore                           # Git ignore rules for Python, Node, DB & secrets
└── README.md                            # Comprehensive technical documentation
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.11+** (Tested with Python 3.14)
- **Node.js v18+** & **npm**

### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows PowerShell:
.\venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt

# Create environment file:
copy .env.example .env
```

### 2. Frontend Setup
```bash
cd ../frontend
npm install
copy .env.example .env
```

### 3. Running the Application

**Option A: Convenience Scripts (PowerShell)**
- Terminal 1 (Backend):
  ```powershell
  .\scripts\run_backend.ps1
  ```
- Terminal 2 (Frontend):
  ```powershell
  .\scripts\run_frontend.ps1
  ```

**Option B: Manual Commands**
- Backend:
  ```powershell
  cd backend
  .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  ```
- Frontend:
  ```powershell
  cd frontend
  npm run dev
  ```

Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).  
Application UI: [http://localhost:5173](http://localhost:5173).

---

## 🧪 Testing

To execute the backend unit test suite:
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

To build and verify the frontend application:
```powershell
cd frontend
npm run build
```

---

## 🗺️ Project Roadmap & Phase Status

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 0** | **Project Analysis & System Architecture** | ✅ Completed & Approved |
| **Phase 1** | **Project Setup & Foundation (FastAPI, SQLite, React, Vite, Tailwind)** | ✅ Completed & Approved |
| **Phase 2** | **Student Interface & Authentication (Dashboard, Socratic Chat, Voice Dock)** | ✅ Completed & Approved |
| **Phase 3** | **Multimodal Input Ingestion Pipeline (Text, Image, PDF, DOCX, Audio, Video)** | ✅ Completed & Approved |
| **Phase 4** | **Educational Knowledge Base Development (Source Registry, Chunking, ChromaDB)** | ✅ Completed & Approved |
| **Phase 5** | **Retrieval-Augmented Generation (RAG: Hybrid Search, Reranking, Citations)** | ✅ Completed (Awaiting Approval) |
| **Phase 6** | **Socratic Tutoring Engine & Symbolic Math Verification (SymPy + Gemini)** | ⏳ Queued for Next Phase |
| **Phase 7** | **Conversational Voice Pipeline & Synchronized Subtitles** | ⏳ Queued |
| **Phase 8** | **Document Summarization, Practice Questions & MCQ Generation** | ⏳ Queued |
| **Phase 9** | **Student Mastery Analytics & Multi-Session Memory** | ⏳ Queued |
| **Phase 10** | **End-to-End Testing, Security Hardening & Documentation** | ⏳ Queued |

---

## 🧠 Phase 5: Retrieval-Augmented Generation (RAG) Pipeline

The RAG pipeline grounds student tutoring answers strictly in verified educational curricula, enforcing verifiable citations and proactive uncertainty communication.

### 1. Multi-Stage RAG Architecture (`/api/v1/rag/`)
- **Stage 1 (Query Processing):** Standardizes bracket LaTeX expressions, classifies query intent (`definition`, `formula_lookup`, `step_by_step_solution`, `conceptual_explanation`), identifies STEM subject domain, and enriches queries via educational synonym expansion.
- **Stage 2 (Hybrid Retrieval):** Dual-engine search combining **ChromaDB Dense Semantic Search** (768-dim cosine similarity) and **Okapi BM25 Sparse Lexical Search** across indexed curriculum chunks.
- **Stage 3 (Reciprocal Rank Fusion & Reranking):** Merges candidate lists using RRF ($RRF(d) = \sum \frac{1}{60 + rank(d)}$) and applies cross-feature reranking with structural heading affinity and formula alignment bonuses.
- **Stage 4 (Context Construction):** Assembles structured reference cards with source titles, chapters, sections, exact page numbers, and canonical URLs.
- **Stage 5 (Grounded Synthesis & Citations):** Instructs the LLM (Gemini 1.5 Flash with deterministic local fallback) to answer strictly from reference cards using numbered footnote citations (`[1]`, `[2]`), without fabricating sources or facts.
- **Uncertainty Communication Guardrail:** When curriculum materials do not contain sufficient context, the pipeline detects the low confidence score and returns a transparent uncertainty response, preventing hallucinated answers on unindexed topics.

### 2. Endpoints
- `POST /api/v1/rag/query`: Primary student inquiry endpoint returning grounded explanation with verified citations.
- `POST /api/v1/rag/retrieve`: Standalone diagnostic retrieval endpoint for inspecting dense, BM25, and rerank scores.
- `POST /api/v1/rag/evaluate`: Automated benchmarking endpoint evaluating recall@k, citation validity, uncertainty accuracy, and latency.

---

## 📚 Phase 4: Educational Knowledge Base Architecture

The educational knowledge base system decouples tutoring answers from pure LLM memory, anchoring all reasoning in legally verified curricula.

### 1. Authoritative Source Registry (`/api/v1/knowledge/sources`)
- Pre-seeded with official, legally compliant educational sources across 6 categories:
  - **NCERT Resources:** Mathematics Grade 10, Physics Grade 11, Chemistry Grade 12 (Fair Dealing).
  - **Government Educational Portals:** ePathshala, NPTEL IIT Madras (CC BY-NC-SA 4.0).
  - **Official University Materials:** OpenStax University Physics & Calculus (CC BY 4.0), MIT OpenCourseWare (CC BY-NC-SA 4.0).
  - **Open Educational Resources (OER):** LibreTexts STEM, Khan Academy.
  - **Official Programming Documentation:** Python 3 Official Docs (PSF License), MDN Web Docs (CC-BY-SA 2.5+).
  - **Academic Research Sources:** arXiv.org Open STEM Preprints.

### 2. Multi-Format Ingestion Pipeline (`/api/v1/knowledge/documents/ingest`)
- **Supported Formats:** PDF (PyMuPDF), DOCX (python-docx), HTML (BeautifulSoup4), and TXT/Markdown.
- **Structural Extraction:** Preserves heading hierarchies (H1-H4), tables as Markdown grids, exact page numbers, and LaTeX equations (`$...$`, `$$...$$`).
- **Boilerplate & Noise Cleaning:** Automatically detects and removes textbook running headers, footers, duplicate lines, and publisher watermarks.

### 3. Concept-Aware Semantic Chunking
- Splits content along natural sentence and concept boundaries without bisecting mathematical formulas.
- Automatically isolates major chapters and sections to prevent concept bleeding across unrelated topics.
- Every chunk embeds immutable metadata: `document_id`, `source_id`, `chapter`, `section`, `page_number`, `extracted_math`, and `sha256_hash`.

### 4. Vector Storage & High-Dimension Embeddings
- **ChromaDB Vector Store:** Embedded persistent HNSW vector indexing located in `./storage/vector_store` under the `educational_curriculum` collection.
- **Dual-Tier Embeddings:** 768-dimensional normalized dense vectors via Google Gemini `text-embedding-004` (cloud) or high-resolution feature hashing projection (offline deterministic fallback).

### 5. Knowledge Lifecycle & Quality Validation
- **Duplicate Document Detection:** Computes SHA-256 file checksums before ingestion; prevents redundant indexing.
- **Document Versioning & Re-indexing:** Increments version (`v1`, `v2`, etc.), automatically purges outdated chunks from ChromaDB and SQLite, and indexes updated materials.
- **Data Quality Audits (`/api/v1/knowledge/quality/reports`):** Validates documents for missing text (< 50 chars), duplicate chunk hashes, unsupported formats, and missing metadata.
- **Curriculum Search (`POST /api/v1/knowledge/query`):** Executes semantic similarity matching and formats verifiable academic citations:
  `"[Source Name], [Chapter], [Section], Page [X] ([Authority]) - License: [License]"`.

---

## 📥 Phase 3: Multimodal Ingestion Pipeline

The multimodal ingestion layer normalizes all student input channels into a single standardized schema: `UnifiedQuestionPayload`.

### 1. Ingestion Endpoints (`/api/v1/ingest/`)
- `POST /text`: Whitespace cleaning, bracket LaTeX delimiter conversion (`\[...\]` $\rightarrow$ `$$...$$`, `\(...\)` $\rightarrow$ `$`), equation detection, and academic domain routing.
- `POST /image`: Pillow contrast stretching, auto-orientation deskew, Gemini 1.5 Flash Vision OCR extracting handwritten formulas and geometric diagrams.
- `POST /pdf`: PyMuPDF layout-aware text extraction, table extraction (`find_tables`), page-indexed academic citation anchors.
- `POST /docx`: `python-docx` heading hierarchy parsing, table restructuring into markdown grids, paragraph grouping.
- `POST /audio`: Direct Gemini multimodal audio STT with offline fallback and student transcript confirmation flag.
- `POST /video`: 30-second keyframe sampling strategy, visual blackboard OCR + audio track transcription fusion, timestamped reference anchors.
- `POST /unified`: Master polymorph endpoint detecting MIME category automatically and dispatching to the appropriate parser.

### 2. File Security Safeguards (`app/core/file_security.py`)
- **Strict Size Limits:** Text (64 KB), Image (20 MB), PDF (50 MB), DOCX (25 MB), Audio (25 MB), Video (100 MB).
- **MIME & Extension Enforcement:** Whitelist-based validation preventing executable uploads and spoofed extensions.
- **Path Sanitization:** Filename sanitization with UUID prefixes preventing directory traversal.
- **Temporary Cleanup:** Automatic resource cleanup on failed extractions.
