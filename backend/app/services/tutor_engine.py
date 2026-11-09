"""Master educational tutor reasoning engine: human conversational pedagogy, concept knowledge, and multi-turn session memory."""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.schemas.tutor import (
    TutorProblemSolveRequest,
    TutorProblemSolveResponse,
    SolutionStep,
    ExplanationLevel,
    TutorChatRequest,
    TutorChatResponse,
)
from app.models.session import StudySession, SessionMessage
from app.services.sympy_solver import sympy_solver
from app.services.rag_service import rag_service
from app.services.answer_validator import answer_validator
from app.services.context_manager import context_manager
from app.schemas.rag import RAGQueryRequest
from app.schemas.validation import AnswerValidationRequest
from app.core.config import settings
from app.core.logging import logger


# Curated high-yield concept knowledge base for offline/local mode
CONCEPT_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "conditional probability": {
        "title": "Conditional Probability",
        "explanation": (
            "Conditional probability is the probability of an event occurring given that another event has already taken place. "
            "We denote it as $P(A|B)$, which you read as **\"the probability of A given B\"**.\n\n"
            "### The Core Intuition\n"
            "Think of it as narrowing down the possibilities. When you receive new information (that event $B$ has already happened), "
            "your entire sample space shrinks to only the outcomes where $B$ occurs.\n\n"
            "For example, imagine rolling a standard fair 6-sided die:\n"
            "- Without any extra information, the probability of rolling a $2$ is $\\frac{1}{6}$, because the sample space is $\\{1, 2, 3, 4, 5, 6\\}$.\n"
            "- Now suppose a friend rolls the die and tells you: *\"The number rolled is an even number.\"*\n"
            "- Your sample space immediately shrinks from $6$ possibilities down to just three: $\\{2, 4, 6\\}$.\n"
            "- Out of those three even numbers, only $2$ satisfies your target, so the probability of rolling a $2$ given that it is even becomes:\n\n"
            "$$P(\\text{Roll 2} \\mid \\text{Even}) = \\frac{1}{3}$$\n\n"
            "Notice how the probability increased from $\\frac{1}{6}$ to $\\frac{1}{3}$ because the new information eliminated the odd numbers.\n\n"
            "### The Mathematical Formula\n"
            "Formally, for any two events $A$ and $B$ where $P(B) > 0$:\n\n"
            "$$P(A|B) = \\frac{P(A \\cap B)}{P(B)}$$\n\n"
            "Where:\n"
            "- **$P(A|B)$** is the conditional probability of $A$ occurring given that $B$ has occurred.\n"
            "- **$P(A \\cap B)$** is the probability that both events $A$ and $B$ happen together (their intersection).\n"
            "- **$P(B)$** is the total probability of event $B$.\n\n"
            "### Key Multiplication Rule\n"
            "Rearranging the formula gives us a direct way to calculate the joint probability of two events:\n\n"
            "$$P(A \\cap B) = P(A|B) \\cdot P(B)$$\n\n"
            "### Independent Events\n"
            "If knowing that $B$ happened gives you no new information about $A$ (meaning the events are independent), then:\n\n"
            "$$P(A|B) = P(A)$$\n\n"
            "For instance, flipping a coin and then rolling a die are independent. Knowing the coin landed on heads does not change the probability of rolling a 4.\n\n"
            "### Practical Applications\n"
            "- **Medical Diagnostics:** Calculating the true likelihood of a disease given a positive lab test result.\n"
            "- **Machine Learning:** Powering algorithms like Naive Bayes for email spam filtering.\n"
            "- **Risk Analysis:** Updating financial or engineering probabilities when new data becomes available (the cornerstone of Bayes' Theorem).\n\n"
            "Does this explanation feel clear, or would you like to walk through a practice problem together?"
        ),
        "steps": [
            SolutionStep(
                step_number=1,
                title="Understand the Sample Space Reduction",
                explanation="Conditional probability updates the sample space from all possible outcomes to only those contained in the conditioning event B.",
                math_expression="S \\to B"
            ),
            SolutionStep(
                step_number=2,
                title="Apply the Governing Definition",
                explanation="The ratio of the joint occurrence P(A and B) to the probability of the conditioning event P(B).",
                math_expression="P(A|B) = \\frac{P(A \\cap B)}{P(B)}"
            ),
            SolutionStep(
                step_number=3,
                title="Verify Edge Cases",
                explanation="P(B) must be strictly greater than zero; if events are independent, P(A|B) simplifies to P(A).",
                math_expression="P(B) > 0"
            )
        ],
        "final_answer": "P(A|B) = \\frac{P(A \\cap B)}{P(B)}"
    },
    "bayes theorem": {
        "title": "Bayes' Theorem",
        "explanation": (
            "Bayes' Theorem is a mathematical formula used to determine conditional probability—specifically, updating our belief "
            "about an event given new evidence.\n\n"
            "### The Formula\n\n"
            "$$P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}$$\n\n"
            "Where:\n"
            "- **$P(A|B)$ (Posterior):** Probability of hypothesis $A$ given evidence $B$.\n"
            "- **$P(B|A)$ (Likelihood):** Probability of observing evidence $B$ if hypothesis $A$ is true.\n"
            "- **$P(A)$ (Prior):** Initial probability of hypothesis $A$ before seeing evidence.\n"
            "- **$P(B)$ (Marginal Likelihood):** Total probability of observing evidence $B$ under all hypotheses.\n\n"
            "### Intuitive Example: Medical Testing\n"
            "If a rare disease affects $1$ in $1000$ people ($P(A) = 0.001$), and a test is $99\\%$ accurate, testing positive does not "
            "mean you have a $99\\%$ chance of having the disease. Because the disease is so rare, false positives from the large healthy population "
            "can outnumber true positives. Bayes' Theorem computes the exact updated probability.\n\n"
            "Would you like to calculate an example with actual numbers?"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Identify Prior and Evidence", explanation="State the baseline probability P(A) and the observed evidence B.", math_expression="P(A), P(B)"),
            SolutionStep(step_number=2, title="Compute Likelihood", explanation="Evaluate P(B|A) and the total probability P(B) across all partitions.", math_expression="P(B) = \\sum P(B|A_i)P(A_i)"),
            SolutionStep(step_number=3, title="Calculate Posterior", explanation="Apply Bayes' formula to compute the updated probability.", math_expression="P(A|B) = \\frac{P(B|A)P(A)}{P(B)}")
        ],
        "final_answer": "P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}"
    },
    "derivative": {
        "title": "The Concept of a Derivative",
        "explanation": (
            "In calculus, a derivative measures how quickly a quantity changes as another quantity changes. "
            "Geometrically, it is the **slope of the tangent line** to a curve at any specific point.\n\n"
            "### The Real-World Intuition\n"
            "Think of driving a car:\n"
            "- Your total distance traveled over time is a function, $s(t)$.\n"
            "- Your average speed over a 2-hour trip is $\\frac{\\Delta s}{\\Delta t}$.\n"
            "- Your **speedometer reading at this exact second** is the **instantaneous rate of change**—that is the derivative, $s'(t) = \\frac{ds}{dt}$.\n\n"
            "### The Formal Limit Definition\n"
            "We calculate the derivative by looking at the slope of a secant line between two points and taking the limit as the distance $h$ between them approaches zero:\n\n"
            "$$f'(x) = \\lim_{h \\to 0} \\frac{f(x + h) - f(x)}{h}$$\n\n"
            "### Common Differentiation Rules\n"
            "- **Power Rule:** $\\frac{d}{dx}[x^n] = n x^{n-1}$\n"
            "- **Constant Rule:** $\\frac{d}{dx}[c] = 0$\n"
            "- **Sum Rule:** $\\frac{d}{dx}[f(x) + g(x)] = f'(x) + g'(x)$\n"
            "- **Product Rule:** $\\frac{d}{dx}[u \\cdot v] = u' v + u v'$\n"
            "- **Chain Rule:** $\\frac{d}{dx}[f(g(x))] = f'(g(x)) \\cdot g'(x)$\n\n"
            "Would you like to differentiate a specific function together?"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Secant Line Slope", explanation="Compute the difference quotient over an interval h.", math_expression="\\frac{f(x+h) - f(x)}{h}"),
            SolutionStep(step_number=2, title="Evaluate the Limit", explanation="Take the limit as h approaches zero to find instantaneous slope.", math_expression="\\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}"),
            SolutionStep(step_number=3, title="Apply Rules", explanation="Use power, product, or chain rules for algebraic simplification.", math_expression="f'(x)")
        ],
        "final_answer": "f'(x) = \\lim_{h \\to 0} \\frac{f(x + h) - f(x)}{h}"
    },
    "integral": {
        "title": "The Concept of an Integral",
        "explanation": (
            "An integral represents the **accumulation of quantities**, most commonly visualized as the **area under a curve** on a graph.\n\n"
            "### Intuition\n"
            "While differentiation breaks down a curve into its instantaneous slope, integration adds up infinitely many tiny slices to find the total.\n"
            "If your car's speedometer shows speed over time, integrating that speed function gives you the **total distance traveled**.\n\n"
            "### Two Forms of Integrals\n"
            "1. **Indefinite Integral (Antiderivative):** Finds a general family of functions whose derivative is $f(x)$:\n"
            "$$\\int f(x) \\, dx = F(x) + C$$\n\n"
            "2. **Definite Integral (Exact Area):** Accumulates the area between $x = a$ and $x = b$:\n"
            "$$\\int_{a}^{b} f(x) \\, dx = F(b) - F(a)$$\n"
            "*(This connection between derivatives and integrals is known as the Fundamental Theorem of Calculus.)*\n\n"
            "Would you like to see a worked integration problem?"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Identify the Integrand", explanation="Set up the function f(x) and boundaries [a, b].", math_expression="\\int f(x) dx"),
            SolutionStep(step_number=2, title="Find the Antiderivative", explanation="Determine F(x) such that F'(x) = f(x).", math_expression="F(x)"),
            SolutionStep(step_number=3, title="Evaluate Boundary Values", explanation="Apply the Fundamental Theorem of Calculus: F(b) - F(a).", math_expression="F(b) - F(a)")
        ],
        "final_answer": "\\int_{a}^{b} f(x) \\, dx = F(b) - F(a)"
    },
    "newton": {
        "title": "Newton's Laws of Motion",
        "explanation": (
            "Sir Isaac Newton established three fundamental physical laws that describe the relationship between the motion of an object "
            "and the forces acting upon it.\n\n"
            "### 1. First Law (The Law of Inertia)\n"
            "An object at rest stays at rest, and an object in motion stays in motion with the same speed and direction, "
            "unless acted upon by an unbalanced external force.\n"
            "*Example: You lurch forward when a car abruptly brakes because your body tends to maintain its forward velocity.*\n\n"
            "### 2. Second Law (Force and Acceleration)\n"
            "The acceleration of an object is directly proportional to the net force acting on it, and inversely proportional to its mass:\n\n"
            "$$\\mathbf{F}_{\\text{net}} = m \\mathbf{a}$$\n\n"
            "Where $\\mathbf{F}$ is force in Newtons (N), $m$ is mass in kilograms (kg), and $\\mathbf{a}$ is acceleration in $\\text{m/s}^2$.\n\n"
            "### 3. Third Law (Action and Reaction)\n"
            "For every action, there is an equal and opposite reaction.\n"
            "*Example: When a rocket engine pushes exhaust gases downward, the gases push the rocket upward with equal force.*\n\n"
            "Which of these three laws would you like to explore further?"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Law of Inertia", explanation="Net force zero implies constant velocity.", math_expression="\\sum F = 0 \\implies v = \\text{const}"),
            SolutionStep(step_number=2, title="Force and Acceleration", explanation="Net force equals mass times acceleration.", math_expression="F = ma"),
            SolutionStep(step_number=3, title="Action and Reaction", explanation="Mutual forces between two bodies are equal in magnitude and opposite in direction.", math_expression="F_{AB} = -F_{BA}")
        ],
        "final_answer": "F = m \\cdot a"
    }
}


class EducationalTutorEngine:
    """Orchestrates natural, conversational problem solving, conceptual explanations, and session memory."""

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
                logger.info("EducationalTutorEngine successfully connected to Google Gemini.")
            except Exception as e:
                logger.warning(f"Could not load Gemini for tutor engine: {e}")

    def _is_conceptual_inquiry(self, query: str) -> bool:
        """Determine if a query is purely asking for a conceptual explanation rather than calculating/solving."""
        q_lower = query.lower().strip()
        # If it explicitly asks to solve, find, calculate, evaluate, or contains an equation/function, it's a problem to solve
        if re.search(r'(=|solve|find\s+the|calculate|evaluate|f\(x\)|x\^|x\*\*|\broots\b)', q_lower):
            return False

        conceptual_starts = (
            "what is", "what are", "what does", "explain", "define", "tell me about",
            "describe", "meaning of", "concept of", "why is", "why does", "how does", "difference between"
        )
        return any(q_lower.startswith(prefix) for prefix in conceptual_starts) or "conditional probability" in q_lower or "bayes" in q_lower

    def _find_concept_match(self, query: str) -> Optional[Dict[str, Any]]:
        """Look for matching concept in curated knowledge base."""
        q_lower = query.lower()
        for key, data in CONCEPT_KNOWLEDGE_BASE.items():
            if key in q_lower:
                return data
        return None

    def solve_problem(
        self,
        request: TutorProblemSolveRequest,
        db: Session
    ) -> TutorProblemSolveResponse:
        """Decompose academic problem or provide natural conversational explanation without robotic templates or emojis."""
        query = request.query.strip()
        level_str = request.level.value if hasattr(request.level, 'value') else str(request.level)

        # 1. Fetch Conversation Context if session_id is active
        turns, is_follow_up, prior_context = context_manager.extract_relevant_context(
            session_id=request.session_id,
            current_query=query,
            db=db
        )
        history_context = [f"{t['role'].upper()}: {t['content']}" for t in turns]

        # 2. Check if query is a conceptual question
        is_concept = self._is_conceptual_inquiry(query)

        # 3. Retrieve verified curriculum knowledge if enabled
        rag_citations = []
        rag_context_text = ""
        if request.include_rag_curriculum:
            try:
                rag_req = RAGQueryRequest(
                    query=query,
                    subject=request.subject,
                    top_k=2
                )
                rag_out = rag_service.execute_rag(rag_req, db=db)
                if rag_out.is_context_sufficient:
                    rag_citations = rag_out.citations
                    rag_context_text = rag_out.context_text
            except Exception as e:
                logger.debug(f"RAG retrieval skipped during problem solving: {e}")

        # 4. Check if LLM (Gemini) can generate a natural, conversational response
        if self._gemini_client:
            try:
                llm_response = self._generate_with_gemini(
                    query=query,
                    level=level_str,
                    subject=request.subject or "STEM",
                    history_context=history_context,
                    rag_context=rag_context_text
                )
                if llm_response:
                    return self._build_llm_response(
                        query=query,
                        llm_text=llm_response,
                        level_str=level_str,
                        rag_citations=rag_citations,
                        history_context=history_context,
                        subject=request.subject
                    )
            except Exception as e:
                logger.warning(f"Gemini tutor call failed: {e}. Using natural local engine.")

        # 5. Handle Conceptual Inquiries locally with high-yield concepts
        if is_concept:
            concept_data = self._find_concept_match(query)
            if concept_data:
                return self._build_concept_response(
                    query=query,
                    concept_data=concept_data,
                    level_str=level_str,
                    rag_citations=rag_citations,
                    history_context=history_context,
                    subject=request.subject
                )

        # 6. Check for Mathematical Equations for SymPy symbolic verification
        has_math_eq = bool(re.search(r'(=|x\^|\bderivative\b|\bintegral\b|\blimit\b|\bfactor\b)', query, re.IGNORECASE))
        sympy_verified = False
        sympy_data = None
        extracted_steps: List[SolutionStep] = []

        if has_math_eq and settings.ENABLE_SYMPY_VERIFICATION:
            try:
                op = "solve"
                if "derivative" in query.lower() or "differentiate" in query.lower():
                    op = "differentiate"
                elif "integral" in query.lower() or "integrate" in query.lower():
                    op = "integrate"
                elif "factor" in query.lower():
                    op = "factor"

                math_res = sympy_solver.solve(query, operation=op, level=request.level)
                if math_res.symbolic_verified:
                    sympy_verified = True
                    sympy_data = {
                        "operation": math_res.operation,
                        "raw_result": math_res.result,
                        "latex_result": math_res.latex_result
                    }
                    extracted_steps = math_res.steps
            except Exception as e:
                logger.debug(f"SymPy direct solver skipped: {e}")

        # 7. Fallback Steps for mathematical/procedural queries
        if not extracted_steps:
            extracted_steps = [
                SolutionStep(
                    step_number=1,
                    title="Understand the Goal",
                    explanation=f"Identify the given information and target outcome for '{query}'.",
                    math_expression=None
                ),
                SolutionStep(
                    step_number=2,
                    title="Apply Key Principles",
                    explanation="Apply the governing mathematical definitions or physical laws.",
                    math_expression=None
                ),
                SolutionStep(
                    step_number=3,
                    title="Solve and Verify",
                    explanation="Compute the result step by step and confirm consistency.",
                    math_expression=None
                )
            ]

        final_ans_str = sympy_data["latex_result"] if (sympy_data and sympy_data.get("latex_result")) else "Solution derived step-by-step."

        # Level-specific pedagogical reasoning
        if level_str == "beginner":
            why_it_works = (
                "Why it works (Intuitive Concept): Think of this problem through real-world balance. "
                "Every algebraic or physical operation performed on one side must balance the other side, "
                "ensuring that the underlying quantities remain invariant."
            )
        elif level_str == "advanced":
            why_it_works = (
                "Why it works (Axiomatic Justification): The solution relies on field properties, linear independence, "
                "and conservation laws. The operational steps preserve equality under rigorous domain constraints."
            )
        else:
            why_it_works = (
                "Why it works: By applying standard mathematical and physical theorems, the unknowns are isolated "
                "through valid equivalence transformations, yielding a unique, verifiable solution."
            )

        # Format natural, human, emoji-free markdown
        md_lines = [
            f"# Step-by-Step Educational Solution\n",
            f"Let's work through this problem step-by-step.\n",
            f"**Problem:** {query}\n"
        ]

        for s in extracted_steps:
            md_lines.append(f"### Step {s.step_number}: {s.title}")
            md_lines.append(s.explanation)
            if s.math_expression:
                md_lines.append(f"\n{s.math_expression}\n")

        md_lines.append("\n### Final Answer")
        md_lines.append(f"> **{final_ans_str}**\n")

        md_lines.append("### Why This Works")
        md_lines.append(why_it_works)

        if rag_citations:
            md_lines.append("\n### Verified Curriculum Citations")
            for c in rag_citations:
                md_lines.append(f"- **{c.citation_label}** {c.citation_text}")

        formatted_md = "\n".join(md_lines)

        val_req = AnswerValidationRequest(
            question=query,
            answer=formatted_md,
            retrieved_chunks=[],
            citations=rag_citations,
            subject=request.subject
        )
        val_res = answer_validator.validate_answer(val_req)

        return TutorProblemSolveResponse(
            problem_understanding=f"We are solving: {query}",
            given_information=["Inquiry: " + query],
            required_result="Exact pedagogical solution",
            steps=extracted_steps,
            final_answer=final_ans_str,
            why_it_works=why_it_works,
            sympy_verified=sympy_verified,
            sympy_details=sympy_data,
            level=level_str,
            formatted_markdown=val_res.sanitized_answer,
            citations=rag_citations,
            conversation_context_used=bool(history_context),
            validation=val_res.model_dump()
        )

    def _generate_with_gemini(
        self,
        query: str,
        level: str,
        subject: str,
        history_context: List[str],
        rag_context: str
    ) -> Optional[str]:
        """Generate a natural, human, conversational response using Gemini."""
        system_prompt = (
            "You are a friendly, encouraging, and clear human academic tutor replying directly to a student in a chat conversation.\n"
            "Speak naturally, warmly, and clearly like a real person talking on chat.\n\n"
            "CRITICAL GUIDELINES:\n"
            "1. Absolutely DO NOT use emojis anywhere in your response (no 🎓, 📌, 📋, 🎯, 🪜, 🏁, 💡, etc.).\n"
            "2. Absolutely DO NOT use robotic boilerplate headers like 'Problem Understanding', 'Given Information', 'Analytical Target', or 'Required Result'.\n"
            "3. Directly answer the student's question in a clear, friendly opening paragraph.\n"
            "4. If explaining a concept, explain the intuition first with a relatable real-world example, followed by formal formulas or definitions in LaTeX.\n"
            "5. Format all mathematical equations in LaTeX: inline with $...$ and display equations with $$...$$.\n"
            "6. If solving a math problem, walk through the steps clearly with numbered steps ('Step 1:', 'Step 2:'), and provide the 'Final Answer'.\n"
            "7. Maintain multi-turn context from prior conversation turns if provided.\n"
            "8. Conclude with an open, friendly follow-up question."
        )

        user_content_parts = []
        if history_context:
            user_content_parts.append("CONVERSATION HISTORY:\n" + "\n".join(history_context[-4:]))
        if rag_context:
            user_content_parts.append("RELEVANT CURRICULUM MATERIAL:\n" + rag_context)
        user_content_parts.append(f"STUDENT QUESTION (Level: {level}, Subject: {subject}):\n{query}")

        full_prompt = "\n\n".join(user_content_parts)
        response = self._gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[system_prompt, full_prompt]
        )
        if response.text and response.text.strip():
            # Clean any stray emojis that the model might produce
            cleaned = re.sub(r'[\U00010000-\U0010ffff]', '', response.text.strip())
            return cleaned
        return None

    def _build_llm_response(
        self,
        query: str,
        llm_text: str,
        level_str: str,
        rag_citations: List[Any],
        history_context: List[str],
        subject: Optional[str]
    ) -> TutorProblemSolveResponse:
        """Wrap Gemini response into standard TutorProblemSolveResponse schema."""
        val_req = AnswerValidationRequest(
            question=query,
            answer=llm_text,
            retrieved_chunks=[],
            citations=rag_citations,
            subject=subject
        )
        val_res = answer_validator.validate_answer(val_req)

        return TutorProblemSolveResponse(
            problem_understanding=f"Inquiry: {query}",
            given_information=["Question: " + query],
            required_result="Natural tutor explanation",
            steps=[
                SolutionStep(
                    step_number=1,
                    title="Concept Explanation",
                    explanation=llm_text[:200] + "...",
                    math_expression=None
                )
            ],
            final_answer="Explanation provided above.",
            why_it_works="Grounded pedagogical explanation.",
            sympy_verified=False,
            sympy_details=None,
            level=level_str,
            formatted_markdown=val_res.sanitized_answer,
            citations=rag_citations,
            conversation_context_used=bool(history_context),
            validation=val_res.model_dump()
        )

    def _build_concept_response(
        self,
        query: str,
        concept_data: Dict[str, Any],
        level_str: str,
        rag_citations: List[Any],
        history_context: List[str],
        subject: Optional[str]
    ) -> TutorProblemSolveResponse:
        """Format a rich, conversational conceptual explanation without emojis or robotic headers."""
        formatted_md = concept_data["explanation"]

        if rag_citations:
            formatted_md += "\n\n### Verified Curriculum Citations\n"
            for c in rag_citations:
                formatted_md += f"- **{c.citation_label}** {c.citation_text}\n"

        if level_str == "beginner":
            why_it_works = f"Why it works (Intuitive Concept): {concept_data['title']} narrows down the sample space to intuitively reflect the new information."
        elif level_str == "advanced":
            why_it_works = f"Why it works (Axiomatic Justification): {concept_data['title']} follows from probability measure spaces and formal mathematical axioms."
        else:
            why_it_works = f"Why it works: {concept_data['title']} updates probability distributions based on observed events."

        val_req = AnswerValidationRequest(
            question=query,
            answer=formatted_md,
            retrieved_chunks=[],
            citations=rag_citations,
            subject=subject
        )
        val_res = answer_validator.validate_answer(val_req)

        return TutorProblemSolveResponse(
            problem_understanding=f"Explaining concept: {concept_data['title']}",
            given_information=["Student inquiry: " + query],
            required_result=f"Clear understanding of {concept_data['title']}",
            steps=concept_data.get("steps", []),
            final_answer=concept_data.get("final_answer", "Concept explained."),
            why_it_works=why_it_works,
            sympy_verified=False,
            sympy_details=None,
            level=level_str,
            formatted_markdown=val_res.sanitized_answer,
            citations=rag_citations,
            conversation_context_used=bool(history_context),
            validation=val_res.model_dump()
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
