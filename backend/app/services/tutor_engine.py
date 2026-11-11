"""Master educational tutor reasoning engine: multi-provider LLM, STEM concepts, SymPy math, RAG, and Wikipedia fallback."""

import re
import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import httpx

from app.schemas.tutor import (
    TutorProblemSolveRequest,
    TutorProblemSolveResponse,
    SolutionStep,
    TutorChatRequest,
    TutorChatResponse,
)
from app.models.session import StudySession, SessionMessage
from app.services.sympy_solver import sympy_solver
from app.services.rag_service import rag_service
from app.services.answer_validator import answer_validator
from app.services.context_manager import context_manager
from app.services.concept_knowledge import find_best_concept
from app.services.code_assistant import safe_code_assistant
from app.schemas.rag import RAGQueryRequest
from app.schemas.validation import AnswerValidationRequest
from app.core.config import settings
from app.core.logging import logger


CHATGPT_STYLE_SYSTEM_PROMPT = (
    "You are a helpful, clear, and knowledgeable AI Tutor chatting directly with a user.\n"
    "Respond naturally, like ChatGPT talking clearly to someone.\n\n"
    "STYLE & FORMATTING RULES:\n"
    "1. Do NOT use emojis anywhere in your response.\n"
    "2. Do NOT use robotic templates like 'Problem Understanding', 'Given Information', 'Analytical Target', or 'Required Result'.\n"
    "3. Start directly with a clear, concise answer or definition.\n"
    "4. When explaining formulas or concepts:\n"
    "   - State the definition clearly.\n"
    "   - Show a '### Formula' section with display LaTeX $$...$$ and a bulleted 'Where:' breakdown.\n"
    "   - Provide a worked '### Example' with numbers.\n"
    "5. Use $...$ for inline math and $$...$$ on its own line for display equations.\n"
    "6. If solving a math equation step-by-step, number the steps ('Step 1:', 'Step 2:') and state 'Final Answer'.\n"
    "7. Preserve conversation continuity if previous turns are provided."
)


class EducationalTutorEngine:
    """Orchestrates live LLMs, rich STEM knowledge, SymPy math solving, RAG, and encyclopedic search."""

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("EducationalTutorEngine connected to Google Gemini.")
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    def _level_why_it_works(self, level_str: str, topic_hint: str = "this principle") -> str:
        """Return pedagogically appropriate rationale across beginner, intermediate, and advanced tiers."""
        if level_str == "beginner":
            return (
                f"Intuitive Concept: {topic_hint} works through real-world balance and intuitive proportions—"
                "each step preserves the underlying relationship without unnecessary complexity."
            )
        if level_str == "advanced":
            return (
                f"Axiomatic Justification: {topic_hint} follows from formal mathematical axioms, algebraic equivalence, "
                "and physical conservation laws under domain constraints."
            )
        return (
            f"Why it works: {topic_hint} applies standard mathematical and scientific theorems through valid transformations."
        )

    def _is_explicit_math_problem(self, query: str) -> bool:
        """Detect if query is asking to compute/solve an explicit equation or calculus problem."""
        q_lower = query.lower().strip()
        if re.search(r'\b(solve|simplify|factor|differentiate|integrate|calculate|evaluate)\b', q_lower):
            # Check if there's an algebraic expression, number, or function rather than pure concept question
            if re.search(r'(=|f\(x\)|x\^|\d)', q_lower) and not re.search(r'^(what is|what are|define|explain)\b', q_lower):
                return True
        if re.search(r'([a-zA-Z0-9\)]\s*=\s*[a-zA-Z0-9\-\+]|x\^\d|\bderivative of f\(|\bintegral of )', q_lower):
            if not re.search(r'^(what is the formula|what is)\b', q_lower):
                return True
        return False

    def _looks_like_code_request(self, query: str) -> bool:
        """Detect Python code snippet debugging or analysis requests."""
        return bool(re.search(r'(\bdef\s+\w+\(|\bfor\s+\w+\s+in\b|\bwhile\s+|```python)', query))

    def _query_llm_providers(
        self,
        query: str,
        level: str,
        subject: str,
        history_context: List[str],
        rag_context: str
    ) -> Optional[str]:
        """Attempt live LLM generation via Gemini, OpenAI, Anthropic, or local Ollama."""
        parts = []
        if history_context:
            parts.append("CONVERSATION HISTORY:\n" + "\n".join(history_context[-6:]))
        if rag_context:
            parts.append("VERIFIED CURRICULUM EXCERPTS:\n" + rag_context)
        parts.append(f"USER QUESTION (Depth: {level}, Subject: {subject}):\n{query}")
        user_prompt = "\n\n".join(parts)

        # 1. Google Gemini
        if self._gemini_client:
            for model_name in ("gemini-2.0-flash", "gemini-1.5-flash"):
                try:
                    resp = self._gemini_client.models.generate_content(
                        model=model_name,
                        contents=[CHATGPT_STYLE_SYSTEM_PROMPT, user_prompt]
                    )
                    if resp and resp.text and resp.text.strip():
                        return re.sub(r'[\U00010000-\U0010ffff]', '', resp.text.strip())
                except Exception as e:
                    logger.debug(f"Gemini {model_name} call failed: {e}")

        # 2. OpenAI API
        if settings.OPENAI_API_KEY:
            try:
                r = httpx.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": CHATGPT_STYLE_SYSTEM_PROMPT},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.4,
                    },
                    timeout=15.0,
                )
                if r.status_code == 200:
                    text = r.json()["choices"][0]["message"]["content"].strip()
                    return re.sub(r'[\U00010000-\U0010ffff]', '', text)
            except Exception as e:
                logger.debug(f"OpenAI call failed: {e}")

        # 3. Local Ollama (if user has Ollama running locally on port 11434)
        if settings.ENVIRONMENT != "testing":
            try:
                tags = httpx.get("http://127.0.0.1:11434/api/tags", timeout=0.4)
                if tags.status_code == 200:
                    models = tags.json().get("models", [])
                    if models:
                        model_id = models[0]["name"]
                        r = httpx.post(
                            "http://127.0.0.1:11434/api/chat",
                            json={
                                "model": model_id,
                                "stream": False,
                                "messages": [
                                    {"role": "system", "content": CHATGPT_STYLE_SYSTEM_PROMPT},
                                    {"role": "user", "content": user_prompt},
                                ],
                            },
                            timeout=20.0,
                        )
                        if r.status_code == 200:
                            text = r.json().get("message", {}).get("content", "").strip()
                            if text:
                                return re.sub(r'[\U00010000-\U0010ffff]', '', text)
            except Exception:
                pass

        return None

    def _lookup_wikipedia_summary(self, query: str) -> Optional[Dict[str, str]]:
        """Fetch accurate encyclopedic overview via Wikipedia REST API when no LLM API key is configured."""
        if settings.ENVIRONMENT == "testing":
            return None

        cleaned = re.sub(
            r'^(what is|what are|who is|who was|explain|define|tell me about|describe|how does|why does)\s+(an?\s+|the\s+)?',
            '',
            query.strip(),
            flags=re.IGNORECASE
        ).strip(" ?!.")
        if not cleaned or len(cleaned) < 2:
            return None

        headers = {"User-Agent": "AIStudentTutor/1.0 (https://github.com/ai-tutor; educational@example.org)"}
        try:
            search_resp = httpx.get(
                "https://en.wikipedia.org/w/rest.php/v1/search/page",
                params={"q": cleaned, "limit": 2},
                headers=headers,
                follow_redirects=True,
                timeout=3.5,
            )
            if search_resp.status_code != 200:
                return None

            pages = search_resp.json().get("pages", [])
            if not pages:
                return None

            page_key = pages[0].get("key")
            if not page_key:
                return None

            summary_resp = httpx.get(
                f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_key}",
                headers=headers,
                follow_redirects=True,
                timeout=3.5,
            )
            if summary_resp.status_code != 200:
                return None

            data = summary_resp.json()
            extract = (data.get("extract") or "").strip()
            title = (data.get("title") or cleaned).strip()
            url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
            if extract and len(extract) > 40:
                return {"title": title, "extract": extract, "url": url}
        except Exception as e:
            logger.debug(f"Wikipedia fallback lookup skipped: {e}")

        return None

    def solve_problem(
        self,
        request: TutorProblemSolveRequest,
        db: Session
    ) -> TutorProblemSolveResponse:
        """Generate clean, human, ChatGPT-style educational answers or SymPy math solutions."""
        query = request.query.strip()
        level_str = request.level.value if hasattr(request.level, 'value') else str(request.level)

        # 1. Conversation history context
        turns, is_follow_up, prior_context = context_manager.extract_relevant_context(
            session_id=request.session_id,
            current_query=query,
            db=db
        )
        history_context = [f"{t['role'].upper()}: {t['content']}" for t in turns]

        # 2. Retrieve verified curriculum context if enabled
        rag_citations = []
        rag_context_text = ""
        if request.include_rag_curriculum:
            try:
                rag_req = RAGQueryRequest(query=query, subject=request.subject, top_k=2)
                rag_out = rag_service.execute_rag(rag_req, db=db)
                if rag_out.is_context_sufficient and rag_out.citations:
                    rag_citations = rag_out.citations
                    rag_context_text = "\n\n".join(c.excerpt for c in rag_out.citations if c.excerpt)
            except Exception as e:
                logger.debug(f"RAG retrieval skipped during problem solving: {e}")

        # 3. Tier 1: Live LLM (Gemini / OpenAI / local Ollama)
        llm_answer = self._query_llm_providers(
            query=query,
            level=level_str,
            subject=request.subject or "General",
            history_context=history_context,
            rag_context=rag_context_text,
        )
        if llm_answer:
            return self._wrap_response(
                query=query,
                formatted_md=llm_answer,
                understanding=query,
                steps=[SolutionStep(step_number=1, title="Explanation", explanation=llm_answer[:180], math_expression=None)],
                final_answer="See explanation above.",
                why_it_works=self._level_why_it_works(level_str, "this explanation"),
                sympy_verified=False,
                sympy_details=None,
                level_str=level_str,
                rag_citations=rag_citations,
                history_context=history_context,
                subject=request.subject,
            )

        # 4. Tier 2: Static Code Analysis if Python snippet is provided
        if self._looks_like_code_request(query):
            code_res = safe_code_assistant.analyze_code(code=query, language="python", level=request.level)
            return self._wrap_response(
                query=query,
                formatted_md=code_res.formatted_markdown,
                understanding="Static Python code analysis",
                steps=[SolutionStep(step_number=1, title="AST Code Inspection", explanation=code_res.explanation, math_expression=None)],
                final_answer=f"Complexity: {code_res.time_complexity}",
                why_it_works=self._level_why_it_works(level_str, "AST complexity analysis"),
                sympy_verified=False,
                sympy_details=None,
                level_str=level_str,
                rag_citations=[],
                history_context=history_context,
                subject="Computer Science",
            )

        # 5. Tier 3: Symbolic Math Solving via SymPy (explicit equations / derivatives / integrals / factors)
        if self._is_explicit_math_problem(query) and settings.ENABLE_SYMPY_VERIFICATION:
            op = "solve"
            q_low = query.lower()
            if "derivative" in q_low or "differentiate" in q_low:
                op = "differentiate"
            elif "integral" in q_low or "integrate" in q_low:
                op = "integrate"
            elif "factor" in q_low:
                op = "factor"
            elif "limit" in q_low:
                op = "limit"

            try:
                math_res = sympy_solver.solve(query, operation=op, level=request.level)
                if math_res.symbolic_verified:
                    sympy_data = {
                        "operation": math_res.operation,
                        "raw_result": math_res.result,
                        "latex_result": math_res.latex_result,
                    }
                    final_ans = math_res.latex_result or math_res.result
                    why = self._level_why_it_works(level_str, "symbolic algebraic derivation")
                    md_lines = [
                        "# Step-by-Step Educational Solution\n",
                        f"Let's solve `{query}` step by step.\n",
                    ]
                    for s in math_res.steps:
                        md_lines.append(f"### Step {s.step_number}: {s.title}")
                        md_lines.append(s.explanation)
                        if s.math_expression:
                            md_lines.append(f"\n{s.math_expression}\n")
                    md_lines.append("\n### Final Answer")
                    md_lines.append(f"**{final_ans}**\n")
                    md_lines.append("### Why This Works")
                    md_lines.append(why)

                    return self._wrap_response(
                        query=query,
                        formatted_md="\n".join(md_lines),
                        understanding=f"Solving: {query}",
                        steps=math_res.steps,
                        final_answer=final_ans,
                        why_it_works=why,
                        sympy_verified=True,
                        sympy_details=sympy_data,
                        level_str=level_str,
                        rag_citations=rag_citations,
                        history_context=history_context,
                        subject=request.subject,
                    )
            except Exception as e:
                logger.debug(f"SymPy solver skipped: {e}")

        # 6. Tier 4: Curated ChatGPT-style STEM Knowledge Base (with fuzzy spelling match)
        # Also resolve anaphoric follow-ups using prior session turns (e.g. "discriminant is negative" after quadratic)
        lookup_query = query
        if is_follow_up and prior_context:
            lookup_query = f"{query} {prior_context[:200]}"
        concept_data = find_best_concept(lookup_query)
        if not concept_data and query != lookup_query:
            concept_data = find_best_concept(query)

        if concept_data:
            md_body = concept_data["explanation"]
            if "discriminant" in query.lower() and "negative" in query.lower():
                md_body = (
                    "When the **discriminant** ($\\Delta = b^2 - 4ac$) is **negative** ($\Delta < 0$), "
                    "we are taking the square root of a negative number inside the quadratic formula:\n\n"
                    "$$x = \\frac{-b \\pm \\sqrt{\\Delta}}{2a}$$\n\n"
                    "This means:\n"
                    "- The equation has **no real roots** (its parabola never crosses the x-axis).\n"
                    "- Instead, it has **two complex / imaginary conjugate roots**:\n\n"
                    "$$x = \\frac{-b \\pm i\\sqrt{4ac - b^2}}{2a}$$\n\n"
                    "### Example\n"
                    "For $x^2 + 2x + 5 = 0$, $\\Delta = 2^2 - 4(1)(5) = -16$.\n"
                    "So the roots are $x = -1 \\pm 2i$."
                )

            if level_str == "beginner":
                md_body += "\n\nIn simple terms, focus first on what each symbol represents before substituting numbers."
            elif level_str == "advanced":
                md_body += "\n\n**Rigorous Note:** These results hold under standard real/complex field axioms and continuity assumptions."

            return self._wrap_response(
                query=query,
                formatted_md=md_body,
                understanding=f"Concept overview: {concept_data['title']}",
                steps=concept_data.get("steps", []),
                final_answer=concept_data.get("final_answer", concept_data["title"]),
                why_it_works=self._level_why_it_works(level_str, concept_data["title"]),
                sympy_verified=False,
                sympy_details=None,
                level_str=level_str,
                rag_citations=rag_citations,
                history_context=history_context,
                subject=request.subject,
            )

        # 7. Tier 5: Live Wikipedia Encyclopedic Lookup for any general topic (outside testing)
        wiki = self._lookup_wikipedia_summary(query)
        if wiki:
            md_lines = [
                f"**{wiki['title']}**\n",
                wiki["extract"],
            ]
            if wiki.get("url"):
                md_lines.append(f"\nReference: [{wiki['title']}]({wiki['url']})")
            md_lines.append("\nLet me know if you would like a simpler explanation, a real-world example, or practice questions on this topic.")
            return self._wrap_response(
                query=query,
                formatted_md="\n".join(md_lines),
                understanding=f"Overview of {wiki['title']}",
                steps=[SolutionStep(step_number=1, title=wiki["title"], explanation=wiki["extract"], math_expression=None)],
                final_answer=wiki["title"],
                why_it_works=self._level_why_it_works(level_str, wiki["title"]),
                sympy_verified=False,
                sympy_details=None,
                level_str=level_str,
                rag_citations=rag_citations,
                history_context=history_context,
                subject=request.subject,
            )

        # 8. Tier 6: Grounded RAG Textbook Context (only when excerpts match query keywords meaningfully)
        q_tokens = {w for w in re.findall(r'[a-z]{4,}', query.lower()) if w not in {"what", "explain", "define", "about", "where", "which"}}
        if rag_citations and q_tokens:
            matching_excerpts = [
                c for c in rag_citations
                if any(tok in c.excerpt.lower() for tok in q_tokens)
            ]
            if matching_excerpts:
                top_cit = matching_excerpts[0]
                excerpt = top_cit.excerpt.strip().replace("\n", " ")
                md_text = (
                    f"Based on **{top_cit.source_name}** (p. {top_cit.page_number}):\n\n"
                    f"{excerpt}\n\n"
                    "Would you like me to break any part of this down further?"
                )
                return self._wrap_response(
                    query=query,
                    formatted_md=md_text,
                    understanding=query,
                    steps=[SolutionStep(step_number=1, title="Curriculum Context", explanation=excerpt, math_expression=None)],
                    final_answer=excerpt[:120],
                    why_it_works=self._level_why_it_works(level_str, "curriculum grounding"),
                    sympy_verified=False,
                    sympy_details=None,
                    level_str=level_str,
                    rag_citations=matching_excerpts,
                    history_context=history_context,
                    subject=request.subject,
                )

        # 9. Honest, clear human fallback (never dump fake "Step 1: Understand the Goal" boilerplate)
        why = self._level_why_it_works(level_str, "transparent uncertainty")
        honest_msg = (
            f"I could not find a verified answer for **\"{query}\"** in the offline knowledge base, "
            "and no live LLM API key (`GEMINI_API_KEY` or `OPENAI_API_KEY`) is configured yet.\n\n"
            "You can either:\n"
            "- Rephrase with a specific math equation (e.g., `solve x^2 - 5x + 6 = 0`), physics/CS/math concept, or paste Python code to analyze.\n"
            "- Or add a free Gemini API key to `backend/.env` (`GEMINI_API_KEY=...`) so I can answer any open-ended question naturally like ChatGPT."
        )
        return self._wrap_response(
            query=query,
            formatted_md=honest_msg,
            understanding=f"Inquiry: {query}",
            steps=[SolutionStep(step_number=1, title="Clarification Needed", explanation=honest_msg, math_expression=None)],
            final_answer="No offline match found; add GEMINI_API_KEY in backend/.env or ask a STEM problem/equation.",
            why_it_works=why,
            sympy_verified=False,
            sympy_details=None,
            level_str=level_str,
            rag_citations=[],
            history_context=history_context,
            subject=request.subject,
        )

    def _wrap_response(
        self,
        query: str,
        formatted_md: str,
        understanding: str,
        steps: List[SolutionStep],
        final_answer: str,
        why_it_works: str,
        sympy_verified: bool,
        sympy_details: Optional[Dict[str, Any]],
        level_str: str,
        rag_citations: List[Any],
        history_context: List[str],
        subject: Optional[str],
    ) -> TutorProblemSolveResponse:
        """Validate response through Phase 7 audit and assemble schema payload."""
        val_req = AnswerValidationRequest(
            question=query,
            answer=formatted_md,
            retrieved_chunks=[],
            citations=rag_citations,
            subject=subject
        )
        val_res = answer_validator.validate_answer(val_req)

        return TutorProblemSolveResponse(
            problem_understanding=understanding,
            given_information=["Inquiry: " + query],
            required_result="Clear educational explanation",
            steps=steps,
            final_answer=final_answer,
            why_it_works=why_it_works,
            sympy_verified=sympy_verified,
            sympy_details=sympy_details,
            level=level_str,
            formatted_markdown=val_res.sanitized_answer,
            citations=rag_citations,
            conversation_context_used=bool(history_context),
            validation=val_res.model_dump(),
        )

    def chat_turn(
        self,
        request: TutorChatRequest,
        db: Session
    ) -> TutorChatResponse:
        """Handle conversational multi-turn follow-up question while maintaining thread context."""
        session = db.query(StudySession).filter(StudySession.id == request.session_id).first()
        if not session:
            session = StudySession(
                id=request.session_id,
                title=f"Tutoring: {request.message[:30]}",
                subject="General STEM"
            )
            db.add(session)
            db.commit()

        user_msg = SessionMessage(
            session_id=session.id,
            sender_role="user",
            content_type="text",
            content=request.message,
            input_type="text",
            extracted_question=request.message
        )
        db.add(user_msg)
        db.commit()

        solve_req = TutorProblemSolveRequest(
            query=request.message,
            session_id=session.id,
            subject=session.subject,
            level=request.level
        )
        solved = self.solve_problem(solve_req, db=db)

        assistant_msg = SessionMessage(
            session_id=session.id,
            sender_role="assistant",
            content_type="text",
            content=solved.formatted_markdown,
            input_type="text",
            extracted_question=request.message,
            citations_json=json.dumps([c.model_dump() for c in solved.citations]) if solved.citations else None
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)

        return TutorChatResponse(
            session_id=session.id,
            message_id=assistant_msg.id,
            response_text=solved.formatted_markdown,
            level=solved.level,
            sympy_verified=solved.sympy_verified,
            citations=solved.citations,
            validation=solved.validation
        )


tutor_engine = EducationalTutorEngine()
