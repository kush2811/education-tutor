"""Master educational tutor engine powered by Google Gemini with session memory and SymPy math verification."""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.models.session import SessionMessage, StudySession
from app.schemas.rag import RAGCitation, RAGQueryRequest
from app.schemas.tutor import (
    SolutionStep,
    TutorChatRequest,
    TutorChatResponse,
    TutorProblemSolveRequest,
    TutorProblemSolveResponse,
)
from app.schemas.validation import AnswerValidationRequest
from app.services.answer_validator import answer_validator
from app.services.context_manager import context_manager
from app.services.rag_service import rag_service
from app.services.sympy_solver import sympy_solver


SUPPORTED_GEMINI_MODELS: Tuple[str, ...] = (
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
)

EDUCATIONAL_TUTOR_SYSTEM_PROMPT = """You are an intelligent, patient, and clear personal AI tutor conversing directly with a student.

Core Teaching Principles:
1. Explain concepts in warm, natural, student-friendly language—like a knowledgeable teacher chatting one-on-one.
2. Provide thoughtful, thorough educational explanations rather than one-line dictionary definitions or encyclopedic snippets.
3. Adjust depth to the student's question and requested pedagogical level (beginner: intuitive analogies and plain terms; intermediate: clear theory, examples, and applications; advanced: formal rigor, edge cases, and deeper analysis).
4. Maintain strict conversation continuity within the session:
   - Interpret follow-ups such as "example", "explain more", "why?", "give code", "give their truth tables", "explain the code line by line", or "give me a practice question" in the exact context of the earlier conversation.
   - Never treat a follow-up prompt like "example" or "why?" as an isolated dictionary lookup.
5. Ask 1-2 brief, helpful clarifying questions ONLY when the student's input is genuinely ambiguous and lacks prior context to resolve it.
6. Never include irrelevant search results, dictionary definitions, or unrequested references/citations/URLs unless the student explicitly asks for sources or citations.
7. Never use emojis anywhere in your response.

Adaptive Response Formatting:
- Choose only the formatting elements that fit the specific question—do NOT force every section into every reply:
  - Topic heading (`## Topic`) when introducing or structuring a concept
  - Clear definition and intuitive simple explanation
  - Step-by-step derivation (`Step 1:`, `Step 2:`, ..., and `Final Answer`) with LaTeX math (`$...$` inline, `$$...$$` display on its own line) when solving mathematical equations or proofs
  - Markdown tables for comparisons or truth tables
  - Concrete examples and real-world practical applications where helpful
  - Syntax-tagged fenced code blocks (such as ```c or ```python) plus clear code walkthroughs for programming requests
  - Key takeaways / important points and a brief summary when covering broader concepts
"""

REFERENCE_REQUEST_PATTERN = re.compile(
    r'\b(cite|citation|citations|reference|references|source|sources|textbook|ncert|oer|curriculum|syllabus|bibliography)\b',
    re.IGNORECASE,
)


class TutorGenerationError(Exception):
    """Explicit error raised when Gemini tutor generation cannot complete."""

    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class EducationalTutorEngine:
    """Orchestrates multi-turn Gemini tutoring, SymPy math checking, and explicit failure reporting."""

    def __init__(self):
        self._gemini_client = None
        self._configured_api_key: Optional[str] = None

    def _get_gemini_client(self):
        """Return a configured Google GenAI client or raise TutorGenerationError if missing."""
        api_key = (settings.GEMINI_API_KEY or "").strip()
        if not api_key:
            self._gemini_client = None
            self._configured_api_key = None
            raise TutorGenerationError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in backend/.env.",
                status_code=503,
            )

        if self._gemini_client is None or self._configured_api_key != api_key:
            try:
                from google import genai
                from google.genai import types

                self._gemini_client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(
                        timeout=30000,
                        retry_options=types.HttpRetryOptions(attempts=1),
                    ),
                )
                self._configured_api_key = api_key
                logger.info("EducationalTutorEngine initialized Google Gemini client.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
                raise TutorGenerationError(
                    f"Failed to initialize Gemini client: {str(e)}",
                    status_code=500,
                ) from e

        return self._gemini_client

    def _candidate_models(self) -> List[str]:
        """Ordered deduplicated list of currently supported Gemini models."""
        configured = (getattr(settings, "GEMINI_MODEL", "") or "").strip()
        ordered: List[str] = []
        if configured:
            ordered.append(configured)
        for model_name in SUPPORTED_GEMINI_MODELS:
            if model_name not in ordered:
                ordered.append(model_name)
        return ordered

    def _level_why_it_works(self, level_str: str, topic_hint: str = "this principle") -> str:
        """Return pedagogically appropriate rationale metadata across difficulty tiers."""
        if level_str == "beginner":
            return (
                f"Intuitive Concept: {topic_hint} builds from concrete intuition and everyday examples "
                "so each idea connects naturally without unnecessary complexity."
            )
        if level_str == "advanced":
            return (
                f"Axiomatic Justification: {topic_hint} follows formal principles, theoretical definitions, "
                "and domain constraints rigorously."
            )
        return (
            f"Why it works: {topic_hint} connects core principles and examples through clear step-by-step reasoning."
        )

    def _explicitly_requests_references(self, query: str) -> bool:
        """Only retrieve or attach curriculum citations when explicitly requested."""
        return bool(REFERENCE_REQUEST_PATTERN.search(query or ""))

    def _is_explicit_math_problem(self, query: str) -> bool:
        """Detect imperative symbolic math requests where SymPy can verify calculations."""
        q_lower = query.lower().strip()
        if re.search(
            r'^(why|how come|explain why|what if|example|give an example|practice)\b',
            q_lower,
        ):
            return False
        if re.search(
            r'\b(solve|simplify|factor|differentiate|integrate|calculate|evaluate|find the derivative|find the integral|find the limit)\b',
            q_lower,
        ):
            if re.search(r'(=|f\(x\)|x\^|\d)', q_lower) and not re.search(
                r'^(what is|what are|define|explain)\b', q_lower
            ):
                return True
        if re.search(
            r'([a-zA-Z0-9\)]\s*=\s*[a-zA-Z0-9\-\+]|x\^\d|\bderivative of f\(|\bintegral of )',
            q_lower,
        ):
            if not re.search(r'^(what is the formula|what is)\b', q_lower):
                return True
        return False

    def _compute_sympy_verification(
        self, query: str, level_enum: Any
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Run SymPy calculation check for explicit symbolic equations to ground Gemini's steps."""
        if not self._is_explicit_math_problem(query) or not settings.ENABLE_SYMPY_VERIFICATION:
            return False, None, None

        q_low = query.lower()
        op = "solve"
        if "derivative" in q_low or "differentiate" in q_low:
            op = "differentiate"
        elif "integral" in q_low or "integrate" in q_low:
            op = "integrate"
        elif "factor" in q_low:
            op = "factor"
        elif "limit" in q_low:
            op = "limit"

        try:
            math_res = sympy_solver.solve(query, operation=op, level=level_enum)
            if math_res.symbolic_verified:
                sympy_data = {
                    "operation": math_res.operation,
                    "raw_result": math_res.result,
                    "latex_result": math_res.latex_result,
                }
                step_notes = "; ".join(
                    f"Step {s.step_number} ({s.title}): {s.explanation}"
                    for s in math_res.steps
                )
                hint = (
                    f"Symbolic Verification ({math_res.operation}): exact result = `{math_res.result}` "
                    f"(LaTeX: `{math_res.latex_result}`). Steps: {step_notes}. "
                    "Present this solution clearly using numbered steps (`Step 1:`, `Step 2:`, ...) and state `Final Answer`."
                )
                return True, sympy_data, hint
        except Exception as e:
            logger.debug(f"SymPy pre-check skipped for query '{query}': {e}")

        return False, None, None

    def _build_gemini_contents(
        self,
        turns: List[Dict[str, str]],
        current_prompt: str,
    ) -> List[Any]:
        """Build valid alternating user/model Content messages for multi-turn Gemini memory."""
        from google.genai import types

        raw_messages: List[Tuple[str, str]] = []
        for t in turns:
            content = (t.get("content") or "").strip()
            if not content:
                continue
            role = "model" if t.get("role") in ("assistant", "model") else "user"
            if raw_messages and raw_messages[-1][0] == role:
                prev_role, prev_text = raw_messages[-1]
                raw_messages[-1] = (prev_role, f"{prev_text}\n\n{content}")
            else:
                raw_messages.append((role, content))

        # Gemini multi-turn history must begin with a user turn when prior messages exist
        while raw_messages and raw_messages[0][0] != "user":
            raw_messages.pop(0)

        # Ensure history ends with a model turn before appending the new user turn
        if raw_messages and raw_messages[-1][0] == "user":
            prev_role, prev_text = raw_messages.pop()
            current_prompt = f"{prev_text}\n\n{current_prompt}"

        contents = [
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=text)],
            )
            for role, text in raw_messages
        ]
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=current_prompt)],
            )
        )
        return contents

    def _classify_gemini_error(self, err: Exception) -> Tuple[int, str, bool]:
        """Map Gemini SDK exception to (http_status, clear_message, should_try_next_model)."""
        status_code = getattr(err, "code", None)
        err_text = str(err)
        err_upper = err_text.upper()

        if status_code in (401, 403) or "API_KEY_INVALID" in err_upper or "API KEY NOT VALID" in err_upper or "PERMISSION_DENIED" in err_upper:
            return (
                502,
                "Gemini API authentication failed: invalid or unauthorized GEMINI_API_KEY. Please verify backend/.env.",
                False,
            )
        if status_code == 400 and "API_KEY" in err_upper:
            return (
                502,
                "Gemini API rejected the configured GEMINI_API_KEY. Please check backend/.env.",
                False,
            )
        if status_code == 429 or "RESOURCE_EXHAUSTED" in err_upper or "QUOTA" in err_upper:
            return (
                429,
                "Gemini API quota or rate limit exceeded. Please wait a moment and try again.",
                True,
            )
        if status_code == 404 or "NOT_FOUND" in err_upper:
            return (
                502,
                f"Configured Gemini model is unavailable: {err_text[:180]}",
                True,
            )
        if status_code in (500, 502, 503, 504) or "DEADLINE_EXCEEDED" in err_upper or "TIMED OUT" in err_upper or "TIMEOUT" in err_upper:
            return (
                504 if status_code == 504 else 503,
                "Gemini AI service timed out or is temporarily unavailable. Please try again.",
                True,
            )
        return (
            502,
            f"Gemini API request failed: {err_text[:220]}",
            False,
        )

    def _generate_with_gemini(
        self,
        query: str,
        level: str,
        subject: str,
        turns: List[Dict[str, str]],
        sympy_hint: Optional[str] = None,
        rag_context: str = "",
        references_requested: bool = False,
    ) -> str:
        """Call Google Gemini using structured multi-turn history and system instructions."""
        from google.genai import types

        client = self._get_gemini_client()

        instruction_addons = [
            f"Current Student Settings -> Pedagogical Depth: {level}; Subject Domain: {subject}."
        ]
        if not references_requested:
            instruction_addons.append(
                "Do NOT attach reference lists, external links, or [1]-style citation markers to this answer."
            )
        if turns:
            instruction_addons.append(
                "Prior turns from this session are included above; answer follow-ups directly in continuity with that discussion."
            )

        system_instruction = f"{EDUCATIONAL_TUTOR_SYSTEM_PROMPT}\n\n" + "\n".join(instruction_addons)

        current_parts = [query]
        if sympy_hint:
            current_parts.append(f"[Internal Math Verification Note]\n{sympy_hint}")
        if rag_context:
            current_parts.append(f"[Requested Curriculum References]\n{rag_context}")
        current_prompt = "\n\n".join(current_parts)

        contents = self._build_gemini_contents(turns=turns, current_prompt=current_prompt)
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
        )

        last_status = 502
        last_message = "Gemini API request failed."

        for model_name in self._candidate_models():
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
                raw_text = (getattr(resp, "text", None) or "").strip()
                if raw_text:
                    # Strip any stray non-BMP emojis to keep output clean and TTS-friendly
                    return re.sub(r'[\U00010000-\U0010ffff]', '', raw_text).strip()

                last_status = 502
                last_message = f"Gemini model '{model_name}' returned an empty response. Please rephrase your question and try again."
                logger.warning(last_message)
            except Exception as err:
                status_code, err_msg, try_next = self._classify_gemini_error(err)
                logger.error(f"Gemini error on model '{model_name}': {err}")
                last_status = status_code
                last_message = err_msg
                if not try_next:
                    raise TutorGenerationError(last_message, status_code=last_status) from err

        raise TutorGenerationError(last_message, status_code=last_status)

    def _extract_solution_steps(self, markdown_text: str) -> List[SolutionStep]:
        """Extract numbered step summaries from Gemini markdown for structured response metadata."""
        matches = re.findall(
            r'(?:^|\n)\s*(?:#{1,4}\s*)?(?:\*\*)?Step\s*(\d+)\s*:\s*([^\n*]+)(?:\*\*)?',
            markdown_text,
            re.IGNORECASE,
        )
        steps: List[SolutionStep] = []
        for idx_str, title in matches[:10]:
            steps.append(
                SolutionStep(
                    step_number=int(idx_str),
                    title=title.strip(),
                    explanation=title.strip(),
                    math_expression=None,
                )
            )
        if steps:
            return steps
        first_line = next((line.strip("#* ") for line in markdown_text.splitlines() if line.strip()), markdown_text[:180])
        return [SolutionStep(step_number=1, title="Explanation", explanation=first_line[:180], math_expression=None)]

    def solve_problem(
        self,
        request: TutorProblemSolveRequest,
        db: Session,
        user_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> TutorProblemSolveResponse:
        """Generate a contextual, educational tutor response via Google Gemini."""
        query = request.query.strip()
        level_str = request.level.value if hasattr(request.level, "value") else str(request.level)

        # 1. Retrieve isolated conversation history for the current session
        try:
            turns, _, _ = context_manager.extract_relevant_context(
                session_id=request.session_id,
                current_query=query,
                db=db,
                user_id=user_id,
                student_id=student_id,
            )
        except PermissionError as pe:
            raise TutorGenerationError(str(pe), status_code=403) from pe

        history_context = [f"{t['role'].upper()}: {t['content']}" for t in turns]

        # 2. Retrieve RAG curriculum context ONLY when the student explicitly requests references/sources
        references_requested = self._explicitly_requests_references(query)
        rag_citations: List[RAGCitation] = []
        rag_context_text = ""
        if request.include_rag_curriculum and references_requested:
            try:
                rag_req = RAGQueryRequest(query=query, subject=request.subject, top_k=3)
                rag_out = rag_service.execute_rag(rag_req, db=db)
                if rag_out.is_context_sufficient and rag_out.citations:
                    rag_citations = rag_out.citations
                    rag_context_text = "\n\n".join(c.excerpt for c in rag_out.citations if c.excerpt)
            except Exception as e:
                logger.warning(f"Requested RAG retrieval skipped: {e}")

        # 3. Pre-verify symbolic math with SymPy when query is an explicit math computation
        sympy_verified, sympy_details, sympy_hint = self._compute_sympy_verification(
            query=query,
            level_enum=request.level,
        )

        # 4. Generate authentic Gemini AI response (raises TutorGenerationError on failure — no silent fallback)
        gemini_markdown = self._generate_with_gemini(
            query=query,
            level=level_str,
            subject=request.subject or "General",
            turns=turns,
            sympy_hint=sympy_hint,
            rag_context=rag_context_text,
            references_requested=references_requested,
        )

        # 5. Validate output safely (consistency, math arithmetic check, Python AST check)
        val_req = AnswerValidationRequest(
            question=query,
            answer=gemini_markdown,
            retrieved_chunks=[],
            citations=rag_citations,
            subject=request.subject,
        )
        val_res = answer_validator.validate_answer(val_req)

        final_answer_text = (
            (sympy_details.get("latex_result") or sympy_details.get("raw_result"))
            if sympy_details
            else "See explanation above."
        )
        steps = self._extract_solution_steps(gemini_markdown)
        why_it_works = self._level_why_it_works(
            level_str,
            request.subject or "this concept",
        )

        return TutorProblemSolveResponse(
            problem_understanding=query,
            given_information=[f"Inquiry: {query}"],
            required_result="Clear educational explanation",
            steps=steps,
            final_answer=final_answer_text,
            why_it_works=why_it_works,
            sympy_verified=sympy_verified,
            sympy_details=sympy_details,
            level=level_str,
            formatted_markdown=val_res.sanitized_answer,
            citations=rag_citations,
            conversation_context_used=bool(history_context),
            validation=val_res.model_dump(),
        )

    def _next_message_timestamps(self, session_id: str, db: Session) -> Tuple[datetime, datetime]:
        """Produce strictly monotonic timestamps so user turns always precede assistant replies."""
        latest = (
            db.query(SessionMessage.created_at)
            .filter(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at.desc())
            .first()
        )
        now = datetime.utcnow()
        if latest and latest[0] is not None and now <= latest[0]:
            now = latest[0] + timedelta(milliseconds=1)
        return now, now + timedelta(milliseconds=1)

    def chat_turn(
        self,
        request: TutorChatRequest,
        db: Session,
        user_id: Optional[str] = None,
        student_id: Optional[str] = None,
    ) -> TutorChatResponse:
        """Handle conversational multi-turn tutor dialogue while keeping strict session isolation."""
        session = db.query(StudySession).filter(StudySession.id == request.session_id).first()
        if session:
            if session.user_id is not None and user_id is not None and session.user_id != user_id:
                raise TutorGenerationError("Access denied: you do not own this study session.", status_code=403)
            if session.user_id is not None and user_id is None:
                raise TutorGenerationError("Authentication required to access this study session.", status_code=403)
            if session.user_id is None and student_id and session.student_id and session.student_id != student_id:
                raise TutorGenerationError("Access denied: session belongs to another student.", status_code=403)

        # Solve using PRIOR session history BEFORE writing the current turn (prevents duplication and orphan rows on error)
        solve_req = TutorProblemSolveRequest(
            query=request.message,
            session_id=session.id if session else None,
            subject=session.subject if session else None,
            level=request.level,
            include_rag_curriculum=self._explicitly_requests_references(request.message),
        )
        solved = self.solve_problem(solve_req, db=db, user_id=user_id, student_id=student_id)

        if not session:
            session = StudySession(
                id=request.session_id,
                user_id=user_id,
                student_id=student_id or "default_student",
                title=f"Tutoring: {request.message[:30]}",
                subject="General STEM",
            )
            db.add(session)
            db.commit()

        user_ts, assistant_ts = self._next_message_timestamps(session.id, db)
        user_msg = SessionMessage(
            session_id=session.id,
            sender_role="user",
            content_type="text",
            content=request.message,
            input_type="text",
            extracted_question=request.message,
            created_at=user_ts,
        )
        assistant_msg = SessionMessage(
            session_id=session.id,
            sender_role="assistant",
            content_type="text",
            content=solved.formatted_markdown,
            input_type="text",
            extracted_question=request.message,
            citations_json=json.dumps([c.model_dump() for c in solved.citations]) if solved.citations else None,
            created_at=assistant_ts,
        )
        db.add_all([user_msg, assistant_msg])
        db.commit()
        db.refresh(assistant_msg)

        return TutorChatResponse(
            session_id=session.id,
            message_id=assistant_msg.id,
            response_text=solved.formatted_markdown,
            level=solved.level,
            sympy_verified=solved.sympy_verified,
            citations=solved.citations,
            validation=solved.validation,
        )


tutor_engine = EducationalTutorEngine()
