"""Pydantic schemas for Phase 6: AI Tutor and Educational Problem Solver."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.schemas.rag import RAGCitation


class ExplanationLevel(str, Enum):
    """Pedagogical depth and explanation complexity."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SolutionStep(BaseModel):
    """A single sequential step in a structured educational problem breakdown."""
    step_number: int
    title: str = Field(..., description="Action title e.g. 'Isolate variable x'")
    explanation: str = Field(..., description="Intuitive explanation of why this step is performed")
    math_expression: Optional[str] = Field(None, description="LaTeX equation for this step e.g. '$$2x = 6$$'")


class TutorProblemSolveRequest(BaseModel):
    """Student request for a structured, multi-level educational explanation."""
    query: str = Field(..., min_length=2, max_length=4000, description="STEM problem, theorem, or question")
    session_id: Optional[str] = Field(None, description="Active study session ID to preserve conversation context")
    subject: Optional[str] = Field(None, description="Subject domain (e.g. Mathematics, Physics, Computer Science)")
    level: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE, description="Pedagogical depth")
    include_rag_curriculum: bool = Field(default=True, description="Ground solution in verified curriculum knowledge")


class TutorProblemSolveResponse(BaseModel):
    """Structured response conforming to educational tutor presentation requirements."""
    problem_understanding: str = Field(..., description="Restatement of the problem in clear pedagogical terms")
    given_information: List[str] = Field(default_factory=list, description="Explicit parameters and constants provided")
    required_result: str = Field(..., description="Clear definition of what must be solved or proven")
    steps: List[SolutionStep] = Field(default_factory=list, description="Numbered step-by-step calculations and rationale")
    final_answer: str = Field(..., description="Conclusive verified final answer with units")
    why_it_works: str = Field(..., description="Conceptual justification of the underlying theorems and principles")
    sympy_verified: bool = Field(default=False, description="Whether mathematical calculations were symbolically verified")
    sympy_details: Optional[Dict[str, Any]] = None
    level: str
    formatted_markdown: str = Field(..., description="Ready-to-render Markdown matching frontend TutorResponse component")
    citations: List[RAGCitation] = Field(default_factory=list)
    conversation_context_used: bool = False
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Answer validation and grounding audit")


class MathSolveRequest(BaseModel):
    """Direct mathematical inquiry for symbolic calculation and step derivation."""
    expression: str = Field(..., min_length=1, description="Mathematical equation, derivative, integral, or statistics problem")
    operation: str = Field(
        default="solve",
        description="One of: 'solve', 'factor', 'expand', 'differentiate', 'integrate', 'limit', 'statistics'"
    )
    variable: str = Field(default="x", description="Independent variable of interest")
    point: Optional[str] = Field(None, description="Evaluation point for limits or definite integrals")
    level: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE)


class MathSolveResponse(BaseModel):
    """Symbolically verified mathematical calculation result with intermediate steps."""
    expression: str
    operation: str
    result: str
    latex_result: str
    steps: List[SolutionStep]
    symbolic_verified: bool
    explanation: str


class CodeAssistRequest(BaseModel):
    """Programming inquiry for safe code explanation, debugging, or algorithmic analysis."""
    code: str = Field(..., max_length=10000, description="Source code snippet")
    language: str = Field(default="python", description="Programming language (e.g. python, javascript, c++)")
    task: str = Field(
        default="explain",
        description="One of: 'explain', 'debug', 'complexity', 'optimize'"
    )
    error_message: Optional[str] = Field(None, description="Optional stack trace or compiler error message")
    level: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE)


class CodeAssistResponse(BaseModel):
    """Safe static code analysis, debugging advice, and complexity breakdown."""
    language: str
    task: str
    syntax_valid: bool
    explanation: str
    detected_bugs: List[str] = Field(default_factory=list)
    fixed_code: Optional[str] = None
    time_complexity: Optional[str] = None
    space_complexity: Optional[str] = None
    educational_advice: str


class StudyAidRequest(BaseModel):
    """Request to generate structured summaries, key points, or revision notes."""
    content: str = Field(..., min_length=10, description="Educational chapter text, notes, or topic")
    aid_type: str = Field(
        default="summary",
        description="One of: 'summary', 'revision_notes', 'definitions', 'important_points'"
    )
    title: Optional[str] = Field(None, description="Topic or chapter title")
    level: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE)


class StudyAidResponse(BaseModel):
    """Structured educational synthesis."""
    title: str
    aid_type: str
    level: str
    summary_text: str
    key_points: List[str] = Field(default_factory=list)
    definitions: Dict[str, str] = Field(default_factory=dict)
    formatted_markdown: str


class PracticeMCQItem(BaseModel):
    """Bloom's taxonomy aligned multiple choice question with distractors."""
    question_id: int
    question: str
    options: List[str] = Field(..., min_length=4, max_length=4, description="Four options [A, B, C, D]")
    correct_option_index: int = Field(..., ge=0, le=3, description="0=A, 1=B, 2=C, 3=D")
    explanation: str = Field(..., description="Explanation of why the correct option is right and others are traps")


class PracticeProblemItem(BaseModel):
    """Worked practice exercise."""
    problem_id: int
    problem_type: str  # 'short_answer', 'long_answer', 'practice_problem'
    question: str
    model_answer: str
    grading_rubric_points: List[str] = Field(default_factory=list)


class PracticeQuestionRequest(BaseModel):
    """Request to generate educational quizzes and exercises from curriculum context."""
    topic_or_content: str = Field(..., min_length=3, description="Topic or textbook chapter content")
    subject: Optional[str] = Field(None, description="Subject domain")
    question_type: str = Field(
        default="mcq",
        description="One of: 'mcq', 'short_answer', 'long_answer', 'practice_problems', 'mixed'"
    )
    count: int = Field(default=3, ge=1, le=10, description="Number of questions to generate")
    difficulty: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE)


class PracticeQuestionResponse(BaseModel):
    """Generated practice worksheet."""
    topic: str
    difficulty: str
    mcqs: List[PracticeMCQItem] = Field(default_factory=list)
    problems: List[PracticeProblemItem] = Field(default_factory=list)
    formatted_markdown: str


class TutorChatRequest(BaseModel):
    """Conversational multi-turn student tutor interaction."""
    session_id: str = Field(..., description="Study session ID preserving conversation thread")
    message: str = Field(..., min_length=1, description="Student follow-up inquiry or response")
    level: ExplanationLevel = Field(default=ExplanationLevel.INTERMEDIATE)


class TutorChatResponse(BaseModel):
    """Conversational tutor response."""
    session_id: str
    message_id: str
    response_text: str
    level: str
    sympy_verified: bool
    citations: List[RAGCitation] = Field(default_factory=list)
    validation: Optional[Dict[str, Any]] = Field(default=None, description="Answer validation and grounding audit")

