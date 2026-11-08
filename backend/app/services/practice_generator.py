"""Educational quiz, MCQ, and practice problem generator with distractor analysis and rubrics."""

import json
from typing import List, Dict, Any, Optional
from app.schemas.tutor import (
    PracticeQuestionRequest,
    PracticeQuestionResponse,
    PracticeMCQItem,
    PracticeProblemItem,
    ExplanationLevel,
)
from app.core.config import settings
from app.core.logging import logger


class EducationalPracticeGenerator:
    """Generates Bloom's taxonomy aligned MCQs, short answers, and worked problems with explanations."""

    def __init__(self):
        self._gemini_client = None
        if settings.GEMINI_API_KEY:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not load Gemini for practice questions: {e}")

    def generate_practice(self, request: PracticeQuestionRequest) -> PracticeQuestionResponse:
        """Create tailored exercises and questions based on input topic or textbook excerpt."""
        topic = request.topic_or_content.strip()
        diff_str = request.difficulty.value if hasattr(request.difficulty, 'value') else str(request.difficulty)

        # 1. Try Gemini generation if client available
        if self._gemini_client:
            try:
                prompt = (
                    f"You are a master STEM examiner creating high-quality assessment questions for {diff_str} students.\n\n"
                    f"TOPIC / EXCERPT:\n{topic[:3000]}\n\n"
                    f"TASK: Generate {request.count} {request.question_type} question(s).\n"
                    "FORMAT AS JSON with keys:\n"
                    "- 'mcqs': list of objects with {'question': str, 'options': [str, str, str, str], 'correct_option_index': int (0-3), 'explanation': str}\n"
                    "- 'problems': list of objects with {'problem_type': str, 'question': str, 'model_answer': str, 'grading_rubric_points': [str]}\n"
                    "Ensure distractors represent typical student conceptual traps or arithmetic errors."
                )
                response = self._gemini_client.models.generate_content(
                    model="gemini-1.5-flash",
                    contents=[prompt]
                )
                if response.text and "{" in response.text:
                    clean_json = response.text.strip().replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(clean_json)
                    return self._parse_json_result(topic, diff_str, parsed)
            except Exception as e:
                logger.warning(f"Gemini practice generation failed: {e}. Falling back to deterministic synthesizer.")

        # 2. Deterministic Practice Question Synthesizer
        return self._generate_local_practice_set(topic, request.question_type, request.count, diff_str)

    def _generate_local_practice_set(
        self,
        topic: str,
        q_type: str,
        count: int,
        diff_str: str
    ) -> PracticeQuestionResponse:
        """Heuristic curriculum practice question generator."""
        mcqs: List[PracticeMCQItem] = []
        problems: List[PracticeProblemItem] = []

        topic_lower = topic.lower()

        # Heuristic questions based on detected STEM domain
        if "motion" in topic_lower or "force" in topic_lower or "physics" in topic_lower or "acceleration" in topic_lower:
            mcqs.append(PracticeMCQItem(
                question_id=1,
                question="According to Newton's Second Law of Motion, what is the mathematical relationship between net force (F), mass (m), and acceleration (a)?",
                options=[
                    "F = m / a",
                    "F = m * a",
                    "F = m * a^2",
                    "F = a / m"
                ],
                correct_option_index=1,
                explanation="Newton's second law explicitly states F = ma. Option A and D invert the variables, while Option C confuses kinetic energy proportionality."
            ))
            mcqs.append(PracticeMCQItem(
                question_id=2,
                question="If a net force of 20 N is applied to an object with a mass of 4 kg, what is the resulting acceleration?",
                options=[
                    "80 m/s^2",
                    "0.2 m/s^2",
                    "5 m/s^2",
                    "16 m/s^2"
                ],
                correct_option_index=2,
                explanation="Using a = F / m = 20 N / 4 kg = 5 m/s^2. Option A mistakenly multiplies 20 * 4 = 80; Option B inverts to 4 / 20 = 0.2."
            ))
            problems.append(PracticeProblemItem(
                problem_id=1,
                problem_type="practice_problem",
                question="A 1000 kg car accelerates uniformly from rest to 20 m/s in 5 seconds. Calculate the net force exerted on the vehicle.",
                model_answer="Step 1: Calculate acceleration: a = (v - u) / t = (20 - 0) / 5 = 4 m/s^2. Step 2: Apply Newton's second law: F = m * a = 1000 kg * 4 m/s^2 = 4000 N.",
                grading_rubric_points=[
                    "Correct formula for acceleration (1 mark)",
                    "Evaluation of a = 4 m/s^2 (1 mark)",
                    "Correct application of F = ma (1 mark)",
                    "Final answer with correct SI units: 4000 N (1 mark)"
                ]
            ))
        elif "quadratic" in topic_lower or "math" in topic_lower or "equation" in topic_lower or "derivative" in topic_lower:
            mcqs.append(PracticeMCQItem(
                question_id=1,
                question="For a quadratic equation ax^2 + bx + c = 0, what does a discriminant of D = b^2 - 4ac > 0 signify?",
                options=[
                    "No real solutions (two complex roots)",
                    "Exactly one real repeated root",
                    "Two distinct real roots",
                    "The equation is linear"
                ],
                correct_option_index=2,
                explanation="When D > 0, the square root produces two distinct real values (+ and -), resulting in two distinct real roots."
            ))
            mcqs.append(PracticeMCQItem(
                question_id=2,
                question="What is the derivative of f(x) = 3x^2 - 5x + 7 with respect to x?",
                options=[
                    "6x - 5",
                    "3x - 5",
                    "6x + 7",
                    "6x^2 - 5"
                ],
                correct_option_index=0,
                explanation="Applying the power rule: d/dx(3x^2) = 6x, d/dx(-5x) = -5, and d/dx(7) = 0. Thus f'(x) = 6x - 5."
            ))
            problems.append(PracticeProblemItem(
                problem_id=1,
                problem_type="short_answer",
                question="Solve the quadratic equation x^2 - 7x + 12 = 0 by factoring.",
                model_answer="Factor into (x - 3)(x - 4) = 0. Setting each factor to zero gives x = 3 and x = 4.",
                grading_rubric_points=[
                    "Identification of factors -3 and -4 (2 marks)",
                    "Final roots x = 3 and x = 4 (2 marks)"
                ]
            ))
        else:
            # Generic STEM practice items
            mcqs.append(PracticeMCQItem(
                question_id=1,
                question=f"Which fundamental principle is central to understanding {topic}?",
                options=[
                    "System conservation and deterministic equations",
                    "Random non-reproducible outcomes",
                    "Arbitrary unit conventions",
                    "Qualitative intuition without mathematical models"
                ],
                correct_option_index=0,
                explanation="Rigorous STEM disciplines rely on conservation laws, empirical verification, and deterministic equations."
            ))
            problems.append(PracticeProblemItem(
                problem_id=1,
                problem_type="short_answer",
                question=f"State the core definition and significance of {topic}.",
                model_answer=f"{topic} provides foundational principles used to model and solve complex STEM phenomena systematically.",
                grading_rubric_points=["Clear conceptual definition (2 marks)", "Academic application (2 marks)"]
            ))

        # Format clean Markdown
        md_lines = [
            f"# 🎯 Practice Worksheet: {topic[:40]}",
            f"**Difficulty Level:** {diff_str.capitalize()} | **Total Exercises:** {len(mcqs) + len(problems)}\n",
            "## 🔘 Part A: Multiple Choice Questions"
        ]
        for mcq in mcqs:
            opts = ["A", "B", "C", "D"]
            md_lines.append(f"**Q{mcq.question_id}. {mcq.question}**")
            for i, opt in enumerate(mcq.options):
                md_lines.append(f"- ({opts[i]}) {opt}")
            md_lines.append(f"> **Answer:** Option ({opts[mcq.correct_option_index]})\n> *Explanation:* {mcq.explanation}\n")

        if problems:
            md_lines.append("## 📝 Part B: Worked Problems & Rubrics")
            for p in problems:
                md_lines.append(f"**Problem {p.problem_id}: {p.question}**\n")
                md_lines.append(f"**Model Solution:**\n{p.model_answer}\n")
                md_lines.append("**Marking Rubric:**")
                for r in p.grading_rubric_points:
                    md_lines.append(f"- [x] {r}")
                md_lines.append("")

        return PracticeQuestionResponse(
            topic=topic[:60],
            difficulty=diff_str,
            mcqs=mcqs,
            problems=problems,
            formatted_markdown="\n".join(md_lines)
        )

    def _parse_json_result(self, topic: str, diff_str: str, parsed: Dict[str, Any]) -> PracticeQuestionResponse:
        """Convert parsed LLM JSON output to typed PracticeQuestionResponse."""
        mcqs = []
        for i, m in enumerate(parsed.get("mcqs", []), 1):
            mcqs.append(PracticeMCQItem(
                question_id=i,
                question=m.get("question", ""),
                options=m.get("options", ["A", "B", "C", "D"]),
                correct_option_index=m.get("correct_option_index", 0),
                explanation=m.get("explanation", "")
            ))

        problems = []
        for j, p in enumerate(parsed.get("problems", []), 1):
            problems.append(PracticeProblemItem(
                problem_id=j,
                problem_type=p.get("problem_type", "short_answer"),
                question=p.get("question", ""),
                model_answer=p.get("model_answer", ""),
                grading_rubric_points=p.get("grading_rubric_points", [])
            ))

        return PracticeQuestionResponse(
            topic=topic[:60],
            difficulty=diff_str,
            mcqs=mcqs,
            problems=problems,
            formatted_markdown=f"Practice worksheet generated with {len(mcqs)} MCQs and {len(problems)} problem(s)."
        )


practice_generator = EducationalPracticeGenerator()
