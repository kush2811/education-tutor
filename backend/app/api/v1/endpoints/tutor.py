"""API endpoints for Phase 6: AI Tutor and Educational Problem Solver."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.tutor import (
    TutorProblemSolveRequest,
    TutorProblemSolveResponse,
    MathSolveRequest,
    MathSolveResponse,
    CodeAssistRequest,
    CodeAssistResponse,
    StudyAidRequest,
    StudyAidResponse,
    PracticeQuestionRequest,
    PracticeQuestionResponse,
    TutorChatRequest,
    TutorChatResponse,
)
from app.services.tutor_engine import tutor_engine
from app.services.sympy_solver import sympy_solver
from app.services.code_assistant import safe_code_assistant
from app.services.study_aid_generator import study_aid_generator
from app.services.practice_generator import practice_generator

router = APIRouter()


@router.post(
    "/solve",
    response_model=TutorProblemSolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate a structured, step-by-step educational problem solution with SymPy verification"
)
def solve_problem(
    request: TutorProblemSolveRequest,
    db: Session = Depends(get_db)
) -> TutorProblemSolveResponse:
    """Decomposes a problem into given info, required result, intermediate steps, verified answer,
    and why it works across Beginner, Intermediate, or Advanced explanation levels."""
    try:
        return tutor_engine.solve_problem(request=request, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Problem solving failed: {str(e)}"
        )


@router.post(
    "/math",
    response_model=MathSolveResponse,
    status_code=status.HTTP_200_OK,
    summary="Direct symbolic mathematical calculation and step derivation using SymPy"
)
def solve_mathematics(
    request: MathSolveRequest
) -> MathSolveResponse:
    """Executes deterministic symbolic algebra, calculus (derivatives, integrals, limits),
    arithmetic, or statistics with intermediate mathematical calculations."""
    try:
        return sympy_solver.solve(
            expression=request.expression,
            operation=request.operation,
            variable=request.variable,
            point=request.point,
            level=request.level
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Math calculation failed: {str(e)}"
        )


@router.post(
    "/code",
    response_model=CodeAssistResponse,
    status_code=status.HTTP_200_OK,
    summary="Safe code explanation, AST-based debugging, and complexity analysis"
)
def assist_programming(
    request: CodeAssistRequest
) -> CodeAssistResponse:
    """Statically analyzes code snippets using AST without execution, detecting bugs, syntax errors,
    and explaining time and space complexity."""
    try:
        return safe_code_assistant.analyze_code(
            code=request.code,
            language=request.language,
            task=request.task,
            error_message=request.error_message,
            level=request.level
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code analysis failed: {str(e)}"
        )


@router.post(
    "/study-aid",
    response_model=StudyAidResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate chapter summaries, revision notes, definitions, and key points"
)
def generate_study_aid(
    request: StudyAidRequest
) -> StudyAidResponse:
    """Synthesizes structured study materials, executive summaries, definitions, and high-yield notes."""
    try:
        return study_aid_generator.generate_study_aid(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Study aid generation failed: {str(e)}"
        )


@router.post(
    "/practice",
    response_model=PracticeQuestionResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate practice questions: MCQs with distractor explanations, short-answer, and rubrics"
)
def generate_practice_questions(
    request: PracticeQuestionRequest
) -> PracticeQuestionResponse:
    """Creates Bloom's taxonomy aligned multiple choice questions, short answers, or worked exercises."""
    try:
        return practice_generator.generate_practice(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Practice question generation failed: {str(e)}"
        )


@router.post(
    "/chat",
    response_model=TutorChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-turn conversational tutor interaction maintaining thread context"
)
def chat_with_tutor(
    request: TutorChatRequest,
    db: Session = Depends(get_db)
) -> TutorChatResponse:
    """Engages in multi-turn tutor dialogue, resolving follow-up questions within the active study session."""
    try:
        return tutor_engine.chat_turn(request=request, db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Tutor chat failed: {str(e)}"
        )
