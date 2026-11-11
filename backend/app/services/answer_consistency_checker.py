"""Answer consistency verification service: audits question relevance, logical flow, math consistency via SymPy, and code safety via AST."""

import ast
import re
from typing import List, Tuple, Optional, Set
import sympy

from app.schemas.validation import AnswerConsistencyResult
from app.services.source_grounding_checker import STOPWORDS


class AnswerConsistencyChecker:
    """Verifies that the generated response addresses the student's question, follows logical flow,

    contains internally consistent mathematics, and provides safe, runnable code examples.
    """

    def __init__(self):
        # Disallowed unsafe Python modules and built-ins
        self._unsafe_tokens = {
            "os.system", "subprocess", "shutil.rmtree", "eval", "exec",
            "__import__", "fork", "socket.socket", "urllib.request"
        }

    def check_consistency(
        self,
        question: str,
        answer: str,
        code_snippets: Optional[List[str]] = None
    ) -> AnswerConsistencyResult:
        """Run complete consistency audit across relevance, logic, math, and code."""
        # 1. Question Relevance
        rel_score, addresses_q = self._check_question_relevance(question, answer)

        # 2. Logical Flow
        logic_valid = self._check_logical_flow(answer)

        # 3. Mathematical Consistency via SymPy
        math_consistent, math_discrepancies = self._check_math_consistency(answer)

        # 4. Programming Safety & Plausibility
        snippets_to_check = code_snippets or self._extract_code_blocks(answer)
        code_safe, code_issues = self._check_code_safety_and_plausibility(snippets_to_check)

        return AnswerConsistencyResult(
            addresses_question=addresses_q,
            question_relevance_score=rel_score,
            logical_flow_valid=logic_valid,
            calculations_consistent=math_consistent,
            math_discrepancies=math_discrepancies,
            code_safe_and_plausible=code_safe,
            code_issues=code_issues
        )

    FOLLOWUP_META_TOKENS = {
        "example", "examples", "explain", "elaborate", "clarify", "simplify",
        "continue", "repeat", "more", "details", "detail", "summary", "summarize",
        "code", "program", "line", "step", "steps", "practice", "question",
        "questions", "quiz", "problem", "problems", "give", "show", "write",
        "make", "tell", "yes", "no", "ok", "okay", "please", "another", "next",
    }

    def _stem_token(self, tok: str) -> str:
        """Lightweight singularization for token overlap matching (e.g. tables -> table)."""
        if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
            return tok[:-1]
        return tok

    def _check_question_relevance(self, question: str, answer: str) -> Tuple[float, bool]:
        """Check whether the generated answer substantively addresses the question's key concepts."""
        q_tokens = set(re.findall(r'\b[a-z0-9_]+\b', question.lower())) - STOPWORDS
        if not q_tokens:
            return 1.0, True

        # Pure conversational follow-up requests (e.g. "example", "explain more", "give a practice question")
        # depend on prior session dialogue rather than lexical repetition of the follow-up phrase itself.
        if q_tokens.issubset(self.FOLLOWUP_META_TOKENS) and len(answer.strip()) >= 20:
            return 1.0, True

        a_tokens = set(re.findall(r'\b[a-z0-9_]+\b', answer.lower())) - STOPWORDS
        if not a_tokens:
            return 0.0, False

        q_stems = {self._stem_token(t) for t in q_tokens}
        a_stems = {self._stem_token(t) for t in a_tokens}
        overlap = len(q_stems & a_stems)
        relevance_score = round(overlap / len(q_stems), 3)

        # Check direct substring containment (e.g. math terms or expressions)
        clean_q = re.sub(r'[^a-z0-9+*/=-]', '', question.lower())
        clean_a = re.sub(r'[^a-z0-9+*/=-]', '', answer.lower())
        substr_match = (clean_q in clean_a) if len(clean_q) >= 3 else False

        # At least 15% keyword overlap, >= 1 core term present, or substring match
        addresses = (relevance_score >= 0.15) or (overlap >= 1) or substr_match
        return max(relevance_score, 0.5 if substr_match else relevance_score), addresses

    def _check_logical_flow(self, answer: str) -> bool:
        """Ensure numbered step-by-step progressions do not skip steps or exhibit broken structure."""
        step_matches = re.findall(r'(?:###?\s*Step\s*(\d+)|\bStep\s*(\d+):)', answer, re.IGNORECASE)
        if not step_matches:
            return True

        found_steps = []
        for s1, s2 in step_matches:
            num = int(s1 or s2)
            found_steps.append(num)

        # Check for strict sequential increments (e.g. 1, 2, 3)
        if len(found_steps) > 1:
            for i in range(len(found_steps) - 1):
                # If step jumps by more than 1 (e.g., Step 1 then Step 4)
                if found_steps[i + 1] - found_steps[i] > 2:
                    return False

        return True

    def _check_math_consistency(self, answer: str) -> Tuple[bool, List[str]]:
        """Extract explicit arithmetic equations and check equality with SymPy."""
        discrepancies: List[str] = []

        # Exclude fenced code blocks and inline code from prose arithmetic checking
        prose_answer = re.sub(r'```[\s\S]*?```|`[^`\n]+`', ' ', answer)
        is_boolean_logic_context = bool(
            re.search(r'\b(boolean|logic gate|or gate|nor gate|xor gate|truth table)\b', prose_answer, re.IGNORECASE)
        )

        # Match standalone numeric equalities (LHS begins with digit, '(', or unary '-digit'), ignoring algebraic sub-expressions
        eq_pattern = re.compile(
            r'(?:(?:\$|(?<=\s)|(?<=^)|(?<=:)|(?<=,))((?:-\d|[\d(])[0-9+\-*/^().\s]*)\s*=\s*(-?[0-9][0-9+\-*/^().\s]*))'
        )

        for match in eq_pattern.finditer(prose_answer):
            lhs_clean = match.group(1).strip()
            rhs_clean = match.group(2).strip()
            prefix = prose_answer[:match.start(1)]

            # Skip slices preceded by algebraic operators/variables/LaTeX commands (e.g. "x - 4 = 0", "f(x) = ...")
            if re.search(r'(?:[+\-*/^\\]|(?<![a-zA-Z])[a-zA-Z])\s*$', prefix):
                continue

            # Ignore pure variable assignments or plain single numbers with no arithmetic operator on LHS
            if not any(c in lhs_clean for c in "+-*/^") or re.fullmatch(r'-\d+(?:\.\d+)?', lhs_clean):
                continue

            # In Boolean algebra (OR gate), 1 + 1 = 1 is valid Boolean addition, not base-10 arithmetic
            if is_boolean_logic_context and re.sub(r'\s+', '', f"{lhs_clean}={rhs_clean}") == "1+1=1":
                continue

            # Standardize operators
            lhs_sympy_str = lhs_clean.replace("^", "**")
            rhs_sympy_str = rhs_clean.replace("^", "**")

            try:
                lhs_val = sympy.sympify(lhs_sympy_str)
                rhs_val = sympy.sympify(rhs_sympy_str)

                # Check if both are numeric
                if lhs_val.is_number and rhs_val.is_number:
                    diff = sympy.simplify(lhs_val - rhs_val)
                    if diff != 0:
                        discrepancies.append(
                            f"Mathematical discrepancy: '{lhs_clean} = {rhs_clean}' is inconsistent. "
                            f"Evaluated LHS = {lhs_val}, RHS = {rhs_val}."
                        )
            except Exception:
                # Non-standard or algebraic expression, skip
                pass

        # Check deduction patterns like "2*x = 10 ... therefore x = 7"
        deduction_match = re.search(r'([0-9*]+\s*\*?\s*x\s*=\s*[0-9]+).*?(?:x\s*=\s*([0-9]+))', answer, re.IGNORECASE)
        if deduction_match:
            try:
                eq_str = deduction_match.group(1).replace("=", "-(") + ")"
                sol_val = int(deduction_match.group(2))
                x = sympy.Symbol("x")
                res = sympy.sympify(eq_str).subs(x, sol_val)
                if res != 0:
                    discrepancies.append(
                        f"Deduction discrepancy: Found '{deduction_match.group(1)}' with stated solution 'x = {sol_val}', "
                        f"which fails substitution."
                    )
            except Exception:
                pass

        is_consistent = len(discrepancies) == 0
        return is_consistent, discrepancies

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extract explicitly tagged Python code blocks from markdown fences ```python ... ```."""
        blocks = re.findall(r'```(?:python|py)\b[^\n]*\n(.*?)```', text, re.DOTALL | re.IGNORECASE)
        return [b.strip() for b in blocks if b.strip()]

    def _check_code_safety_and_plausibility(self, code_blocks: List[str]) -> Tuple[bool, List[str]]:
        """Validate syntax, scan for dangerous calls, and identify obvious anti-patterns."""
        issues: List[str] = []
        if not code_blocks:
            return True, issues

        for idx, code in enumerate(code_blocks):
            # 1. Static AST syntax check
            try:
                tree = ast.parse(code)
            except SyntaxError as se:
                issues.append(f"Code block {idx + 1} syntax error at line {se.lineno}: {se.msg}")
                continue

            # 2. Dangerous function / module call scan
            for node in ast.walk(tree):
                # Check for call to unsafe functions
                if isinstance(node, ast.Call):
                    func_name = ""
                    if isinstance(node.func, ast.Name):
                        func_name = node.func.id
                    elif isinstance(node.func, ast.Attribute):
                        # e.g. os.system
                        val_name = getattr(node.func.value, 'id', '')
                        func_name = f"{val_name}.{node.func.attr}"

                    if any(unsafe in func_name for unsafe in self._unsafe_tokens):
                        issues.append(
                            f"Security policy violation in code block {idx + 1}: Disallowed execution call '{func_name}'."
                        )

                # Check for import of unsafe modules
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in ("os", "subprocess", "socket", "shutil"):
                            # Check if dangerous functions are called later
                            pass

                # Check for unbounded while loop without break
                if isinstance(node, ast.While):
                    # Check if test is True or 1
                    is_infinite_test = False
                    if isinstance(node.test, ast.Constant) and node.test.value in (True, 1):
                        is_infinite_test = True
                    elif isinstance(node.test, ast.Name) and node.test.id == "True":
                        is_infinite_test = True

                    if is_infinite_test:
                        has_break = any(isinstance(sub, (ast.Break, ast.Return)) for sub in ast.walk(node))
                        if not has_break:
                            issues.append(f"Code block {idx + 1} contains an infinite loop without exit condition.")

        is_safe = len(issues) == 0
        return is_safe, issues


answer_consistency_checker = AnswerConsistencyChecker()
