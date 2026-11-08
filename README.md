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
        AudioUI["Voice Input & Audio Playback"]
    end

    subgraph API_Gateway ["FastAPI Backend Services"]
        Router["API v1 Gateway (/api/v1)"]
        SessionMgr["Session & Conversation Manager"]
        Orchestrator["Tutor Flow Orchestrator"]
    end

    subgraph AI_Core ["Multimodal AI & Verification Layer"]
        VisionOCR["Multimodal Vision / Diagram OCR (Gemini)"]
        SocraticTutor["Socratic Dialogue Engine"]
        SymPyEngine["SymPy Symbolic Math Verifier"]
        VoiceEngine["Whisper STT / Edge-TTS"]
    end

    subgraph Persistence ["Data & Vector Storage"]
        SQLiteDB[("SQLite Database (Async SQLAlchemy)")]
        VectorStore[("ChromaDB Vector Store (Curriculum RAG)")]
        AssetStorage[("Uploaded Images & Audio Files")]
    end

    Client -->|HTTP / WebSocket| Router
    Router --> SessionMgr
    Router --> Orchestrator
    Orchestrator --> AI_Core
    SessionMgr --> SQLiteDB
    AI_Core --> SymPyEngine
    AI_Core --> VectorStore
    Router --> AssetStorage
```

---

## 📁 Project Directory Structure

```text
ai-tutor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── health.py        # System health & DB readiness endpoint
│   │   │       │   └── session.py       # Tutoring session & message CRUD
│   │   │       └── router.py            # Aggregated v1 API router
│   │   ├── core/
│   │   │   ├── config.py                # Pydantic Settings & environment config
│   │   │   └── logging.py               # Structured application logger
│   │   ├── db/
│   │   │   ├── base.py                  # SQLAlchemy declarative base
│   │   │   └── session.py               # Async engine and sessionmaker
│   │   ├── models/
│   │   │   └── session.py               # StudySession & SessionMessage ORM models
│   │   ├── schemas/
│   │   │   ├── health.py                # Health check response schemas
│   │   │   └── session.py               # Session & Message request/response schemas
│   │   └── main.py                      # FastAPI app factory, CORS & lifespan
│   ├── tests/
│   │   ├── conftest.py                  # Pytest fixtures & async test client
│   │   └── test_api.py                  # Health check & session lifecycle test suite
│   ├── requirements.txt                 # Backend Python dependencies
│   └── .env.example                     # Backend environment template
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx        # Multi-turn chat with LaTeX math rendering
│   │   │   ├── Header.tsx               # App header with live backend status indicator
│   │   │   ├── MathRenderer.tsx         # KaTeX formula renderer for $...$ and $$...$$
│   │   │   ├── SessionList.tsx          # Study sessions sidebar with creation modal
│   │   │   └── WhiteboardCanvas.tsx     # Interactive student scratchpad & canvas
│   │   ├── services/
│   │   │   └── api.ts                   # Type-safe API client for backend communication
│   │   ├── types/
│   │   │   └── index.ts                 # Shared TypeScript interfaces
│   │   ├── App.tsx                      # Main application view & state orchestrator
│   │   ├── index.css                    # Tailwind CSS base & utilities
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

**Option A: Using Convenience Scripts (PowerShell)**
- Terminal 1 (Backend):
  ```powershell
  .\scripts\run_backend.ps1
  ```
- Terminal 2 (Frontend):
  ```powershell
  .\scripts\run_frontend.ps1
  ```

**Option B: Manual Execution**
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

Interactive API documentation will be available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).  
The web application UI will be accessible at [http://localhost:5173](http://localhost:5173).

---

## 🧪 Testing

To execute the backend unit test suite:
```powershell
cd backend
.\venv\Scripts\python.exe -m pytest tests/ -v
```

---

## 🗺️ Project Roadmap & Phase Status

| Phase | Description | Status |
| :--- | :--- | :--- |
| **Phase 1** | **Project Scaffolding, Architecture Baseline & Environment Configuration** | ✅ Completed |
| **Phase 2** | **Multimodal Ingestion Pipeline (Image/Diagram OCR, PDF & Math Parsing)** | ⏳ Pending Approval |
| **Phase 3** | **Socratic Tutoring Engine & Symbolic Math Verification (SymPy + Gemini)** | ⏳ Queued |
| **Phase 4** | **Conversational Voice Pipeline (Whisper STT + Edge-TTS)** | ⏳ Queued |
| **Phase 5** | **Knowledge Retrieval & Verifiable RAG System (ChromaDB + Textbook Indexing)**| ⏳ Queued |
| **Phase 6** | **Interactive Multimodal Student UI & Whiteboard Integration** | ⏳ Queued |
| **Phase 7** | **Student Mastery Analytics & Multi-Session Memory** | ⏳ Queued |
| **Phase 8** | **End-to-End Testing, Security Hardening & Documentation** | ⏳ Queued |
