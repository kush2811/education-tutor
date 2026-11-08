"""Automated unit test suite for Phase 6: AI Tutor and Educational Problem Solver."""

import pytest
from sqlalchemy.orm import Session

from app.models.session import StudySession, SessionMessage
from app.services.sympy_solver import sympy_solver
from app.services.code_assistant import safe_code_assistant
from app.services.study_aid_generator import study_aid_generator
from app.services.practice_generator import practice_generator
from app.services.tutor_engine import tutor_engine
from app.schemas.tutor import (
    TutorProblemSolveRequest,
    ExplanationLevel,
    MathSolveRequest,
    CodeAssistRequest,
    StudyAidRequest,
    PracticeQuestionRequest,
    TutorChatRequest,
)


def test_sympy_algebraic_solving():
    """Verify symbolic quadratic equation solving and factorization with steps."""
    # 1. Quadratic solving
    res = sympy_solver.solve("x^2 - 5*x + 6 = 0", operation="solve")
    assert res.symbolic_verified is True
    assert "2" in res.result and "3" in res.result
    assert len(res.steps) >= 3
    # Check discriminant step
    step2 = res.steps[1]
    assert "Discriminant" in step2.title or "\\Delta" in step2.math_expression

    # 2. Factorization
    res_fact = sympy_solver.solve("x^2 - 9", operation="factor")
    assert res_fact.symbolic_verified is True
    assert "(x - 3)*(x + 3)" in res_fact.result or "(x + 3)*(x - 3)" in res_fact.result


def test_sympy_calculus_differentiation_and_integration():
    """Verify symbolic derivatives, definite/indefinite integrals, and limits."""
    # 1. Derivative
    res_diff = sympy_solver.solve("3*x^3 - 4*x + 5", operation="differentiate")
    assert res_diff.symbolic_verified is True
    assert "9*x**2 - 4" in res_diff.result or "9*x^2 - 4" in res_diff.result
    assert len(res_diff.steps) == 3

    # 2. Indefinite Integral
    res_int = sympy_solver.solve("2*x + 1", operation="integrate")
    assert res_int.symbolic_verified is True
    assert "x**2 + x" in res_int.result or "x^2 + x" in res_int.result
    assert "+ C" in res_int.latex_result

    # 3. Definite Integral
    res_def_int = sympy_solver.solve("3*x^2", operation="integrate", point="0, 2")
    assert res_def_int.symbolic_verified is True
    assert res_def_int.result == "8"

    # 4. Limit
    res_lim = sympy_solver.solve("sin(x)/x", operation="limit", point="0")
    assert res_lim.symbolic_verified is True
    assert res_lim.result == "1"


def test_sympy_arithmetic_and_statistics():
    """Verify exact rational arithmetic and statistics (mean, median, variance, std dev)."""
    # 1. Arithmetic evaluation
    res_arith = sympy_solver.solve("1/2 + 2/3", operation="arithmetic")
    assert res_arith.symbolic_verified is True
    assert res_arith.result == "7/6"

    # 2. Statistics evaluation
    res_stat = sympy_solver.solve("10, 20, 30, 40, 50", operation="statistics")
    assert res_stat.symbolic_verified is True
    assert "Mean=30" in res_stat.result
    assert "Median=30" in res_stat.result
    assert len(res_stat.steps) == 3


def test_safe_code_assistant_ast_debugging_and_complexity():
    """Verify safe AST code analysis, syntax error diagnostics, bug detection, and complexity estimation."""
    # 1. Syntax Error diagnostic without execution
    bad_syntax_code = "def add(a, b\n    return a + b"
    res_syntax = safe_code_assistant.analyze_code(bad_syntax_code, language="python")
    assert res_syntax.syntax_valid is False
    assert len(res_syntax.detected_bugs) >= 1
    assert "SyntaxError" in res_syntax.detected_bugs[0]

    # 2. Anti-pattern: Mutable default argument
    mutable_arg_code = "def append_item(x, target=[]):\n    target.append(x)\n    return target"
    res_mutable = safe_code_assistant.analyze_code(mutable_arg_code, language="python")
    assert res_mutable.syntax_valid is True
    assert any("mutable default" in bug.lower() for bug in res_mutable.detected_bugs)

    # 3. Complexity: Single loop -> O(n)
    linear_code = "def find_max(items):\n    m = items[0]\n    for x in items:\n        if x > m:\n            m = x\n    return m"
    res_linear = safe_code_assistant.analyze_code(linear_code, language="python")
    assert "O(n)" in res_linear.time_complexity

    # 4. Complexity: Nested loops -> O(n^2)
    nested_code = "def bubble_sort(arr):\n    n = len(arr)\n    for i in range(n):\n        for j in range(n - i - 1):\n            if arr[j] > arr[j+1]:\n                arr[j], arr[j+1] = arr[j+1], arr[j]"
    res_nested = safe_code_assistant.analyze_code(nested_code, language="python")
    assert "O(n^2)" in res_nested.time_complexity


def test_explanation_levels(db_session: Session):
    """Verify distinct pedagogical depth across Beginner, Intermediate, and Advanced levels."""
    problem = "Solve the equation 2*x^2 - 8 = 0"

    # 1. Beginner Level
    res_beg = tutor_engine.solve_problem(
        TutorProblemSolveRequest(query=problem, level=ExplanationLevel.BEGINNER),
        db=db_session
    )
    assert res_beg.level == "beginner"
    assert "Intuitive Concept" in res_beg.why_it_works
    assert res_beg.sympy_verified is True

    # 2. Advanced Level
    res_adv = tutor_engine.solve_problem(
        TutorProblemSolveRequest(query=problem, level=ExplanationLevel.ADVANCED),
        db=db_session
    )
    assert res_adv.level == "advanced"
    assert "Axiomatic Justification" in res_adv.why_it_works


def test_study_aid_generator():
    """Verify synthesis of executive summaries, key points, definitions, and revision notes."""
    content = (
        "Newton's laws of motion are three basic laws of classical mechanics. "
        "The first law is defined as the law of inertia. "
        "The second law states that net force is directly proportional to the rate of change of momentum. "
        "The third law states that forces always occur in equal and opposite pairs."
    )
    req = StudyAidRequest(
        content=content,
        aid_type="revision_notes",
        title="Newtonian Mechanics"
    )
    res = study_aid_generator.generate_study_aid(req)
    assert res.title == "Newtonian Mechanics"
    assert len(res.key_points) >= 1
    assert "Revision Notes" in res.formatted_markdown
    assert "law of inertia" in res.formatted_markdown.lower()


def test_practice_question_generator():
    """Verify Bloom's taxonomy aligned MCQ generation with options and distractor rationales."""
    req = PracticeQuestionRequest(
        topic_or_content="Newton's second law of motion and acceleration",
        subject="Physics",
        question_type="mcq",
        count=2
    )
    res = practice_generator.generate_practice(req)
    assert len(res.mcqs) >= 1
    first_mcq = res.mcqs[0]
    assert len(first_mcq.options) == 4
    assert first_mcq.correct_option_index in [0, 1, 2, 3]
    assert len(first_mcq.explanation) > 10
    assert "Practice Worksheet" in res.formatted_markdown


def test_tutor_conversation_context(db_session: Session):
    """Verify multi-turn conversation context tracking and session isolation."""
    # 1. Create a study session
    session = StudySession(
        id="test-session-001",
        title="Calculus Derivatives Review",
        subject="Mathematics"
    )
    db_session.add(session)
    db_session.commit()

    # 2. Send first message
    chat_req_1 = TutorChatRequest(
        session_id="test-session-001",
        message="Find the derivative of f(x) = x^2 - 4x"
    )
    res_1 = tutor_engine.chat_turn(chat_req_1, db=db_session)
    assert res_1.session_id == "test-session-001"
    assert "Final Answer" in res_1.response_text

    # 3. Verify messages stored in SQLite
    msgs = db_session.query(SessionMessage).filter(SessionMessage.session_id == "test-session-001").all()
    assert len(msgs) == 2  # 1 user + 1 assistant

    # 4. Send follow-up message using conversation thread
    chat_req_2 = TutorChatRequest(
        session_id="test-session-001",
        message="Why is the derivative of -4x equal to -4?"
    )
    res_2 = tutor_engine.chat_turn(chat_req_2, db=db_session)
    assert res_2.session_id == "test-session-001"

    msgs_after = db_session.query(SessionMessage).filter(SessionMessage.session_id == "test-session-001").all()
    assert len(msgs_after) == 4


def test_tutor_api_endpoints(client, db_session: Session):
    """Test REST API endpoints for solve, math, code, study aid, practice, and chat."""
    # 1. POST /api/v1/tutor/solve
    res_solve = client.post("/api/v1/tutor/solve", json={
        "query": "Solve x^2 - 16 = 0",
        "level": "intermediate"
    })
    assert res_solve.status_code == 200
    solve_json = res_solve.json()
    assert solve_json["sympy_verified"] is True
    assert "Step-by-Step" in solve_json["formatted_markdown"]

    # 2. POST /api/v1/tutor/math
    res_math = client.post("/api/v1/tutor/math", json={
        "expression": "differentiate 4*x^3 - 2*x",
        "operation": "differentiate"
    })
    assert res_math.status_code == 200
    assert "12*x**2 - 2" in res_math.json()["result"] or "12*x^2 - 2" in res_math.json()["result"]

    # 3. POST /api/v1/tutor/code
    res_code = client.post("/api/v1/tutor/code", json={
        "code": "for i in range(10):\n    print(i)",
        "language": "python"
    })
    assert res_code.status_code == 200
    assert res_code.json()["syntax_valid"] is True
    assert "O(n)" in res_code.json()["time_complexity"]

    # 4. POST /api/v1/tutor/study-aid
    res_aid = client.post("/api/v1/tutor/study-aid", json={
        "content": "Kinematics describes the motion of points, bodies, and systems without considering forces.",
        "aid_type": "summary",
        "title": "Kinematics Overview"
    })
    assert res_aid.status_code == 200
    assert "Study Guide" in res_aid.json()["formatted_markdown"]

    # 5. POST /api/v1/tutor/practice
    res_prac = client.post("/api/v1/tutor/practice", json={
        "topic_or_content": "Newton's Laws of Motion",
        "question_type": "mcq",
        "count": 2
    })
    assert res_prac.status_code == 200
    assert len(res_prac.json()["mcqs"]) >= 1

    # 6. POST /api/v1/tutor/chat
    res_chat = client.post("/api/v1/tutor/chat", json={
        "session_id": "api-session-test",
        "message": "Explain what a derivative represents."
    })
    assert res_chat.status_code == 200
    assert "api-session-test" == res_chat.json()["session_id"]

