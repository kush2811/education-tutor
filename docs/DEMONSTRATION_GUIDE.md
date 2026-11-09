# Interactive Student Demonstration Guide

This guide provides step-by-step instructions to showcase the full capabilities of the **AI-Powered Multimodal Educational Tutor & Problem Solver**.

You can run the demonstration in two ways:
1. **Automated Programmatic Walkthrough:** Runs the end-to-end Python test script verifying all 10 stages in terminal output.
2. **Interactive Web Interface Walkthrough:** Demonstrates the student journey through the modern React UI.

---

## 1. Automated Programmatic Walkthrough (Terminal)

The repository includes a self-contained demonstration script that automates every single phase of the student interaction.

### How to Run:
```bash
# Navigate to backend directory with active virtual environment
cd backend

# Execute the 10-step walkthrough script
python ../scripts/demonstration_walkthrough.py
```

### What It Executes & Verifies:
- **Step 1: Student Asks Question via Text:** Submits a quadratic equation ($x^2 - 5x + 6 = 0$), normalizes input, and detects mathematical formulas.
- **Step 2: Student Uploads an Image Worksheet:** Synthesizes and uploads a geometry diagram image, verifies file magic bytes, and extracts text via OCR.
- **Step 3: Student Uploads a PDF Document:** Ingests a physics worksheet, extracts text across page layout blocks, and tracks page numbers.
- **Step 4: Student Submits Recorded Audio Question:** Processes audio bytes through Speech-to-Text, isolating spoken inquiries safely.
- **Step 5: AI Retrieves Educational Knowledge via Hybrid RAG:** Queries ChromaDB dense embeddings and BM25 sparse index with Reciprocal Rank Fusion, outputting textbook citations.
- **Step 6: AI Explains Solution Step by Step with SymPy Verification:** Verifies computation symbolically with SymPy ($x=2, 3$), generates 4 Socratic pedagogical steps, and explains "Why it works".
- **Step 7: Student Listens to Synthesized Neural Voice:** Synthesizes natural audio using Microsoft Neural Edge-TTS (`en-US-AriaNeural`).
- **Step 8: Subtitles Synchronize with Millisecond Alignment:** Prints sentence-level and word-level timestamps aligned to audio playback.
- **Step 9: Student Asks an Anaphoric Follow-Up Question:** Evaluates contextual follow-up query (*"What if that constant term was negative instead?"*) within the conversation thread.
- **Step 10: Student Opens Persistent Conversation History:** Retrieves all 10 turns (user questions, multimodal tags, AI answers, and audio URLs) from the database.

---

## 2. Interactive Web Interface Walkthrough (Browser)

### Prerequisites:
1. Start the FastAPI backend:
   ```bash
   cd backend
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
2. Start the Vite React frontend:
   ```bash
   cd frontend
   npm run dev
   ```
3. Open `http://localhost:5173` in your browser.

---

### Step-by-Step Interactive Script:

#### 1. Student Onboarding & Login
- Click **"Get Started"** or navigate to the **Login** tab.
- Click **"Sign Up"** and create an account:
  - Name: `Alex Mercer`
  - Grade: `Grade 11 STEM`
  - Email: `alex@example.edu`
  - Password: `Password123!`
- The student is automatically authenticated and redirected to the **Student Dashboard**.

#### 2. Student Dashboard
- Note the personalized metrics: Active Sessions, Topics Mastered, and Explanation Rigor selector (`Beginner`, `Intermediate`, `Advanced`).
- Select `Intermediate`.
- Click **"New Tutoring Session"** or select **"Tutor Chat"** in the navigation header.

#### 3. Step 1: Text Question & Symbolic Solving
- In the chat box, type:
  ```text
  Solve for x: x^2 - 5*x + 6 = 0
  ```
- Click **Send**.
- Observe the response breakdown:
  - 📌 **Problem Understanding**
  - 🔍 **Given Information & Goal**
  - 📝 **Step-by-Step Derivation**
  - ✅ **Final Answer:** $x = 2, 3$ (annotated with a green *"SymPy Verified"* badge)
  - 💡 **Why It Works**

#### 4. Step 2: Image Worksheet Upload
- Click the **Paperclip / Image** upload icon.
- Select a photo of a math or geometry worksheet from your disk.
- Watch the upload progress indicator and real-time OCR extraction preview.
- Click **Submit** to watch the AI solve the diagram.

#### 5. Step 3: PDF Document Ingestion
- Click the **File Upload** button and select a PDF file (e.g., textbook chapter or syllabus excerpt).
- The document is parsed, page numbers are identified, and the tutor generates a curriculum-aligned explanation citing specific pages.

#### 6. Step 4: Spoken Voice Question
- Click the **Microphone** icon in the chat prompt.
- Allow browser microphone access and ask:
  *"Can you explain Newton's second law?"*
- Click **Stop Recording**. Review the live transcribed speech, then press **Send**.

#### 7. Step 5 & 6: Curriculum RAG & Citations
- In the answer, observe the **Source References** collapsible panel at the bottom.
- Expand it to see verified citations:
  - *NCERT Class 11 Physics, Chapter 5 (Laws of Motion), Page 93* with clickable source links.

#### 8. Step 7 & 8: Neural Voice & Synchronized Subtitles
- Click the **"Listen to Answer"** button on the tutor's response card.
- The **Voice Dock** slides in at the bottom of the screen:
  - The tutor speaks in natural neural audio.
  - Notice the **Current Sentence** highlighting in real time.
  - Notice the **Spoken Word Glow** advancing synchronously with audio ticks.
  - Drag the **Audio Scrubber** bar to seek backward or forward; observe the text highlight jump instantly to match the spoken word.
  - Toggle playback speed from `1.0x` to `1.5x` and verify pitch preservation.

#### 9. Step 9: Contextual Follow-Up Question
- In the chat prompt, type:
  ```text
  What happens if the force is doubled?
  ```
- Notice that the tutor remembers the previous inquiry about Newton's Second Law ($F=ma$) and directly deduces that acceleration doubles, without needing the original formula restated.

#### 10. Step 10: Conversation History & Multi-Session Management
- Look at the **Conversation History Sidebar** on the left.
- Click **Rename Session** to label it *"Physics & Kinematics Review"*.
- Click **"+ New Session"** to start a separate conversation on Biology or Python.
- Click back on *"Physics & Kinematics Review"*; verify all previous turns, mathematical equations, and audio player states are instantly restored.
