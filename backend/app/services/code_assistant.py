"""Safe static code analysis, AST parsing, pedagogical debugging, and algorithmic complexity analyzer."""

import ast
from typing import List, Dict, Any, Optional, Tuple
from app.schemas.tutor import CodeAssistResponse, ExplanationLevel


class SafeCodeAssistant:
    """Provides safe code explanation, AST-based debugging, and complexity analysis without executing arbitrary code."""

    def analyze_code(
        self,
        code: str,
        language: str = "python",
        task: str = "explain",
        error_message: Optional[str] = None,
        level: ExplanationLevel = ExplanationLevel.INTERMEDIATE
    ) -> CodeAssistResponse:
        """Statically inspect submitted source code and return educational tutoring feedback."""
        lang = language.lower().strip()

        if lang in ["python", "py"]:
            return self._analyze_python_ast(code, task, error_message, level)
        else:
            return self._analyze_generic_code(code, lang, task, error_message, level)

    def _analyze_python_ast(
        self,
        code: str,
        task: str,
        error_message: Optional[str],
        level: ExplanationLevel
    ) -> CodeAssistResponse:
        """Parse Python source code using Abstract Syntax Tree (AST) safely without execution."""
        syntax_valid = True
        detected_bugs: List[str] = []
        fixed_code: Optional[str] = None
        tree = None

        # 1. Safe AST Syntax Parsing
        try:
            tree = ast.parse(code)
        except SyntaxError as se:
            syntax_valid = False
            detected_bugs.append(f"SyntaxError at line {se.lineno}, col {se.offset}: {se.msg}")
            # Generate beginner-friendly explanation
            educational_adv = (
                f"Your code stopped because Python encountered a syntax error on line {se.lineno}: '{se.text.strip() if se.text else ''}'. "
                f"Hint: Check for missing colons (:), unclosed parentheses, or indentation mismatch."
            )
            return CodeAssistResponse(
                language="python",
                task=task,
                syntax_valid=False,
                explanation=f"Syntax analysis failed: {se.msg}",
                detected_bugs=detected_bugs,
                fixed_code=None,
                time_complexity="N/A (Syntax Error)",
                space_complexity="N/A (Syntax Error)",
                educational_advice=educational_adv
            )

        # 2. Static AST Visitor Inspections
        max_loop_depth = 0
        has_recursion = False
        func_names = set()
        dangerous_calls = []

        class StaticCodeVisitor(ast.NodeVisitor):
            def __init__(self):
                self.current_loop_depth = 0
                self.max_depth = 0
                self.has_recursion = False
                self.funcs = set()
                self.bugs = []
                self.dangerous = []

            def visit_FunctionDef(self, node):
                self.funcs.add(node.name)
                # Check for mutable default arguments
                for arg in node.args.defaults:
                    if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                        self.bugs.append(f"Function '{node.name}' uses mutable default argument (antipattern in Python). Use None instead.")
                self.generic_visit(node)

            def visit_For(self, node):
                self.current_loop_depth += 1
                self.max_depth = max(self.max_depth, self.current_loop_depth)
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_While(self, node):
                self.current_loop_depth += 1
                self.max_depth = max(self.max_depth, self.current_loop_depth)
                # Check for while True without break
                has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                if isinstance(node.test, ast.Constant) and node.test.value is True and not has_break:
                    self.bugs.append("Potential infinite loop detected: 'while True' with no explicit 'break' statement.")
                self.generic_visit(node)
                self.current_loop_depth -= 1

            def visit_Call(self, node):
                # Recursion check
                if isinstance(node.func, ast.Name) and node.func.id in self.funcs:
                    self.has_recursion = True
                # Dangerous calls check
                if isinstance(node.func, ast.Name) and node.func.id in ["eval", "exec"]:
                    self.dangerous.append(f"Security Alert: Use of '{node.func.id}()' can execute arbitrary code.")
                self.generic_visit(node)

        visitor = StaticCodeVisitor()
        visitor.visit(tree)
        detected_bugs.extend(visitor.bugs)
        if visitor.dangerous:
            detected_bugs.extend(visitor.dangerous)

        # 3. Complexity Estimation
        if visitor.max_depth == 0:
            time_comp = "O(1) Constant Time"
        elif visitor.max_depth == 1:
            time_comp = "O(n) Linear Time"
        elif visitor.max_depth == 2:
            time_comp = "O(n^2) Quadratic Time"
        else:
            time_comp = f"O(n^{visitor.max_depth}) Polynomial Time"

        if visitor.has_recursion:
            time_comp += " (Recursive call stack)"
            space_comp = "O(depth) Call Stack Space"
        else:
            space_comp = "O(1) Auxiliary Space"

        # 4. Educational Advice & Explanation
        lines = code.splitlines()
        explanation_parts = [
            f"The Python script contains {len(lines)} lines and defines {len(visitor.funcs)} function(s): {', '.join(visitor.funcs) or 'Main execution block'}.",
            f"Static Analysis Status: {len(detected_bugs)} potential bug(s) or warning(s) found.",
            f"Loop Depth: {visitor.max_depth} level(s) of iteration, indicating an estimated time complexity of {time_comp}."
        ]
        if error_message:
            explanation_parts.append(f"Error Diagnostic: The runtime message '{error_message}' indicates an issue during evaluation.")

        educational_advice = (
            "Pedagogical Recommendation: Always test with empty inputs, single-element collections, and negative numbers. "
            "Ensure loop termination conditions advance toward the base case on every iteration."
        )

        return CodeAssistResponse(
            language="python",
            task=task,
            syntax_valid=syntax_valid,
            explanation=" ".join(explanation_parts),
            detected_bugs=detected_bugs,
            fixed_code=code,
            time_complexity=time_comp,
            space_complexity=space_comp,
            educational_advice=educational_advice
        )

    def _analyze_generic_code(
        self,
        code: str,
        language: str,
        task: str,
        error_message: Optional[str],
        level: ExplanationLevel
    ) -> CodeAssistResponse:
        """Static inspection for non-Python languages (JavaScript, C++, Java)."""
        lines = code.splitlines()
        # Heuristic loop depth counting
        loop_keywords = ["for (", "while (", "for(", "while("]
        loop_count = sum(any(kw in line for kw in loop_keywords) for line in lines)

        if loop_count == 0:
            time_comp = "O(1) Constant Time"
        elif loop_count == 1:
            time_comp = "O(n) Linear Time"
        else:
            time_comp = f"O(n^{loop_count}) Polynomial Time"

        detected_bugs = []
        if error_message:
            detected_bugs.append(f"Compiler/Runtime Notice: {error_message}")

        return CodeAssistResponse(
            language=language,
            task=task,
            syntax_valid=True,
            explanation=f"Analyzed {len(lines)} lines of {language.upper()} code.",
            detected_bugs=detected_bugs,
            fixed_code=code,
            time_complexity=time_comp,
            space_complexity="O(1) Auxiliary Space",
            educational_advice="Review array indices for off-by-one errors (< vs <=) and ensure memory allocations are freed."
        )


safe_code_assistant = SafeCodeAssistant()

