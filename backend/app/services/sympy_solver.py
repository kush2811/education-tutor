"""Symbolic mathematical problem solver and verifier using SymPy."""

import re
from typing import Dict, Any, List, Optional
import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

from app.schemas.tutor import SolutionStep, MathSolveResponse, ExplanationLevel
from app.core.logging import logger

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)


class SymPyMathSolver:
    """Solves and verifies mathematical problems across arithmetic, algebra, calculus, and statistics."""

    def __init__(self):
        self.transformations = TRANSFORMATIONS

    def clean_math_string(self, expr_str: str) -> str:
        """Sanitize mathematical input for safe SymPy parsing."""
        clean = expr_str.strip()
        # Strip outer delimiters $ or $$
        clean = re.sub(r'^\${1,2}|\${1,2}$', '', clean).strip()
        # Strip leading English operational verbs if present (including colons e.g. "Solve for x:")
        clean = re.sub(r'^(?:differentiate|derivative\s+of|find\s+the\s+derivative\s+of|integrate|integral\s+of|solve\s+for\s+\w+:?|solve:?|factor|expand|evaluate|calculate)\s*', '', clean, flags=re.IGNORECASE).strip()
        # Standardize LaTeX brackets
        clean = clean.replace(r'\[', '').replace(r'\]', '')
        # Replace LaTeX fractions \frac{a}{b} -> (a)/(b)
        clean = re.sub(r'\\frac\{([^\}]+)\}\{([^\}]+)\}', r'(\1)/(\2)', clean)
        # Replace ^ with **
        clean = clean.replace('^', '**')
        # Replace \cdot or \times with *
        clean = clean.replace(r'\cdot', '*').replace(r'\times', '*')
        # Strip \left and \right
        clean = clean.replace(r'\left', '').replace(r'\right', '')
        return clean

    def solve(
        self,
        expression: str,
        operation: str = "solve",
        variable: str = "x",
        point: Optional[str] = None,
        level: ExplanationLevel = ExplanationLevel.INTERMEDIATE
    ) -> MathSolveResponse:
        """Route to specialized mathematical solver and return step-by-step derivation."""
        op = operation.lower().strip()
        cleaned_expr = self.clean_math_string(expression)

        try:
            if op in ["solve", "algebra", "roots"]:
                return self._solve_algebraic_equation(cleaned_expr, variable, level)
            elif op in ["differentiate", "derivative", "diff"]:
                return self._solve_derivative(cleaned_expr, variable, level)
            elif op in ["integrate", "integral"]:
                return self._solve_integral(cleaned_expr, variable, point, level)
            elif op in ["limit"]:
                return self._solve_limit(cleaned_expr, variable, point, level)
            elif op in ["factor"]:
                return self._solve_factorization(cleaned_expr, level)
            elif op in ["expand"]:
                return self._solve_expansion(cleaned_expr, level)
            elif op in ["statistics", "stats"]:
                return self._solve_statistics(cleaned_expr, level)
            elif op in ["arithmetic", "evaluate"]:
                return self._solve_arithmetic(cleaned_expr, level)
            else:
                return self._solve_algebraic_equation(cleaned_expr, variable, level)
        except Exception as e:
            logger.warning(f"SymPy evaluation error for '{expression}' with op '{operation}': {e}")
            return MathSolveResponse(
                expression=expression,
                operation=operation,
                result=f"Calculation notice: {str(e)}",
                latex_result=expression,
                steps=[
                    SolutionStep(
                        step_number=1,
                        title="Input Parsing",
                        explanation=f"Attempted symbolic parsing of expression '{expression}'. Please verify standard algebraic syntax.",
                        math_expression=f"$${expression}$$"
                    )
                ],
                symbolic_verified=False,
                explanation="The mathematical expression could not be solved symbolically."
            )

    def _solve_algebraic_equation(self, expr_str: str, var_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Solve polynomial, linear, or quadratic equations."""
        var = sp.Symbol(var_str)
        steps: List[SolutionStep] = []

        if "=" in expr_str:
            lhs_str, rhs_str = expr_str.split("=", 1)
            lhs = parse_expr(lhs_str, transformations=self.transformations)
            rhs = parse_expr(rhs_str, transformations=self.transformations)
            eq_expr = lhs - rhs
            steps.append(SolutionStep(
                step_number=1,
                title="Standard Form Equation",
                explanation="Move all terms to the left-hand side to set the equation to zero: $f(x) = 0$.",
                math_expression=f"$${sp.latex(lhs)} = {sp.latex(rhs)} \\implies {sp.latex(eq_expr)} = 0$$"
            ))
        else:
            eq_expr = parse_expr(expr_str, transformations=self.transformations)
            steps.append(SolutionStep(
                step_number=1,
                title="Identify Expression",
                explanation="Set the polynomial expression equal to zero to determine its roots.",
                math_expression=f"$${sp.latex(eq_expr)} = 0$$"
            ))

        # Check if quadratic in var
        degree = sp.degree(eq_expr, gen=var) if eq_expr.is_polynomial(var) else None

        if degree == 2:
            # Quadratic step breakdown
            poly = sp.Poly(eq_expr, var)
            coeffs = poly.all_coeffs()
            a, b, c = coeffs[0], coeffs[1], coeffs[2]
            disc = b**2 - 4*a*c
            steps.append(SolutionStep(
                step_number=2,
                title="Calculate Discriminant",
                explanation=f"Identify coefficients: $a = {sp.latex(a)}$, $b = {sp.latex(b)}$, $c = {sp.latex(c)}$. Compute $\\Delta = b^2 - 4ac$.",
                math_expression=f"$$\\Delta = ({sp.latex(b)})^2 - 4({sp.latex(a)})({sp.latex(c)}) = {sp.latex(disc)}$$"
            ))

            factored = sp.factor(eq_expr)
            if factored != eq_expr:
                steps.append(SolutionStep(
                    step_number=3,
                    title="Factorization",
                    explanation="Express the quadratic as a product of linear binomial factors.",
                    math_expression=f"$${sp.latex(factored)} = 0$$"
                ))

        solutions = sp.solve(eq_expr, var)
        latex_sols = [sp.latex(s) for s in solutions]
        sol_str = ", ".join(latex_sols) if latex_sols else "No real solutions"

        steps.append(SolutionStep(
            step_number=len(steps) + 1,
            title="Determine Final Roots",
            explanation=f"Solve for {var_str} by evaluating the factors or applying the quadratic formula.",
            math_expression=f"$${var_str} = {sol_str}$$"
        ))

        return MathSolveResponse(
            expression=expr_str,
            operation="solve",
            result=f"{var_str} = {', '.join(str(s) for s in solutions)}",
            latex_result=f"$${var_str} = {sol_str}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"The equation {expr_str} yields roots: {sol_str}."
        )

    def _solve_derivative(self, expr_str: str, var_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Symbolic differentiation with step breakdown."""
        var = sp.Symbol(var_str)
        f_expr = parse_expr(expr_str, transformations=self.transformations)
        derivative = sp.diff(f_expr, var)

        steps = [
            SolutionStep(
                step_number=1,
                title="Identify Function",
                explanation=f"Given function $f({var_str})$ to differentiate with respect to ${var_str}$.",
                math_expression=f"$$f({var_str}) = {sp.latex(f_expr)}$$"
            ),
            SolutionStep(
                step_number=2,
                title="Apply Differentiation Rules",
                explanation="Apply standard differentiation rules (Power rule, Sum rule, Product/Chain rule).",
                math_expression=f"$$\\frac{{d}}{{d{var_str}}} \\left[{sp.latex(f_expr)}\\right]$$"
            ),
            SolutionStep(
                step_number=3,
                title="Final Derivative",
                explanation=f"Compute the rate of change $f'({var_str})$.",
                math_expression=f"$$f'({var_str}) = {sp.latex(derivative)}$$"
            )
        ]

        return MathSolveResponse(
            expression=expr_str,
            operation="differentiate",
            result=str(derivative),
            latex_result=f"$$\\frac{{d}}{{d{var_str}}} [{sp.latex(f_expr)}] = {sp.latex(derivative)}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"The derivative of {expr_str} with respect to {var_str} is {sp.latex(derivative)}."
        )

    def _solve_integral(self, expr_str: str, var_str: str, point: Optional[str], level: ExplanationLevel) -> MathSolveResponse:
        """Symbolic indefinite or definite integration."""
        var = sp.Symbol(var_str)
        f_expr = parse_expr(expr_str, transformations=self.transformations)

        if point and ("," in point or ":" in point):
            # Definite integral with bounds a, b
            sep = "," if "," in point else ":"
            a_str, b_str = point.split(sep, 1)
            a = parse_expr(a_str.strip(), transformations=self.transformations)
            b = parse_expr(b_str.strip(), transformations=self.transformations)
            result_expr = sp.integrate(f_expr, (var, a, b))
            antiderivative = sp.integrate(f_expr, var)

            steps = [
                SolutionStep(
                    step_number=1,
                    title="Definite Integral Setup",
                    explanation=f"Evaluate definite integral between lower bound ${sp.latex(a)}$ and upper bound ${sp.latex(b)}$.",
                    math_expression=f"$$\\int_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} {sp.latex(f_expr)} \\, d{var_str}$$"
                ),
                SolutionStep(
                    step_number=2,
                    title="Find Antiderivative",
                    explanation=f"Compute primitive function $F({var_str}) = \\int f({var_str}) d{var_str}$.",
                    math_expression=f"$$F({var_str}) = {sp.latex(antiderivative)}$$"
                ),
                SolutionStep(
                    step_number=3,
                    title="Fundamental Theorem of Calculus",
                    explanation=f"Evaluate $F(b) - F(a) = F({sp.latex(b)}) - F({sp.latex(a)})$.",
                    math_expression=f"$$[{sp.latex(antiderivative)}]_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} = {sp.latex(result_expr)}$$"
                )
            ]
            latex_res = f"$$\\int_{{{sp.latex(a)}}}^{{{sp.latex(b)}}} {sp.latex(f_expr)} \\, d{var_str} = {sp.latex(result_expr)}$$"
        else:
            # Indefinite integral
            result_expr = sp.integrate(f_expr, var)
            steps = [
                SolutionStep(
                    step_number=1,
                    title="Set Up Indefinite Integral",
                    explanation="Find the family of antiderivatives for the given integrand.",
                    math_expression=f"$$\\int {sp.latex(f_expr)} \\, d{var_str}$$"
                ),
                SolutionStep(
                    step_number=2,
                    title="Integrate Term by Term",
                    explanation="Apply standard integration formulas and append constant of integration $C$.",
                    math_expression=f"$$\\int {sp.latex(f_expr)} \\, d{var_str} = {sp.latex(result_expr)} + C$$"
                )
            ]
            latex_res = f"$$\\int {sp.latex(f_expr)} \\, d{var_str} = {sp.latex(result_expr)} + C$$"

        return MathSolveResponse(
            expression=expr_str,
            operation="integrate",
            result=str(result_expr),
            latex_result=latex_res,
            steps=steps,
            symbolic_verified=True,
            explanation=f"The integral evaluates to {sp.latex(result_expr)}."
        )

    def _solve_limit(self, expr_str: str, var_str: str, point: Optional[str], level: ExplanationLevel) -> MathSolveResponse:
        """Evaluate limit of function as variable approaches point."""
        var = sp.Symbol(var_str)
        f_expr = parse_expr(expr_str, transformations=self.transformations)
        pt = parse_expr(point.strip(), transformations=self.transformations) if point else sp.Integer(0)
        lim_val = sp.limit(f_expr, var, pt)

        steps = [
            SolutionStep(
                step_number=1,
                title="Identify Limit Expression",
                explanation=f"Evaluate the limit of $f({var_str})$ as ${var_str} \\to {sp.latex(pt)}$.",
                math_expression=f"$$\\lim_{{{var_str} \\to {sp.latex(pt)}}} {sp.latex(f_expr)}$$"
            ),
            SolutionStep(
                step_number=2,
                title="Compute Limit Value",
                explanation="Determine convergence value through direct substitution or L'Hôpital's rule.",
                math_expression=f"$$\\lim_{{{var_str} \\to {sp.latex(pt)}}} {sp.latex(f_expr)} = {sp.latex(lim_val)}$$"
            )
        ]

        return MathSolveResponse(
            expression=expr_str,
            operation="limit",
            result=str(lim_val),
            latex_result=f"$$\\lim_{{{var_str} \\to {sp.latex(pt)}}} {sp.latex(f_expr)} = {sp.latex(lim_val)}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"The limit as {var_str} approaches {sp.latex(pt)} is {sp.latex(lim_val)}."
        )

    def _solve_factorization(self, expr_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Algebraic factorization."""
        expr = parse_expr(expr_str, transformations=self.transformations)
        factored = sp.factor(expr)
        steps = [
            SolutionStep(
                step_number=1,
                title="Original Expression",
                explanation="Identify common factors or binomial patterns.",
                math_expression=f"$${sp.latex(expr)}$$"
            ),
            SolutionStep(
                step_number=2,
                title="Factored Form",
                explanation="Express as irreducible factors over the rational field.",
                math_expression=f"$${sp.latex(factored)}$$"
            )
        ]
        return MathSolveResponse(
            expression=expr_str,
            operation="factor",
            result=str(factored),
            latex_result=f"$${sp.latex(factored)}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"{expr_str} factors into {sp.latex(factored)}."
        )

    def _solve_expansion(self, expr_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Polynomial expansion."""
        expr = parse_expr(expr_str, transformations=self.transformations)
        expanded = sp.expand(expr)
        steps = [
            SolutionStep(
                step_number=1,
                title="Expand Expression",
                explanation="Distribute terms and combine like monomials.",
                math_expression=f"$${sp.latex(expr)} = {sp.latex(expanded)}$$"
            )
        ]
        return MathSolveResponse(
            expression=expr_str,
            operation="expand",
            result=str(expanded),
            latex_result=f"$${sp.latex(expanded)}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"{expr_str} expands to {sp.latex(expanded)}."
        )

    def _solve_arithmetic(self, expr_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Exact rational arithmetic evaluation."""
        expr = parse_expr(expr_str, transformations=self.transformations)
        exact_val = sp.Rational(expr) if expr.is_rational else expr
        steps = [
            SolutionStep(
                step_number=1,
                title="Arithmetic Evaluation",
                explanation="Evaluate using order of operations (PEMDAS/BODMAS) with exact rational precision.",
                math_expression=f"$${expr_str} = {sp.latex(exact_val)}$$"
            )
        ]
        return MathSolveResponse(
            expression=expr_str,
            operation="arithmetic",
            result=str(exact_val),
            latex_result=f"$${sp.latex(exact_val)}$$",
            steps=steps,
            symbolic_verified=True,
            explanation=f"The arithmetic expression simplifies to {sp.latex(exact_val)}."
        )

    def _solve_statistics(self, expr_str: str, level: ExplanationLevel) -> MathSolveResponse:
        """Calculate statistical mean, median, sample variance, and standard deviation."""
        # Parse comma-separated numbers: e.g. "12, 15, 18, 22, 25"
        raw_nums = [n.strip() for n in expr_str.replace(";", ",").split(",") if n.strip()]
        data = [sp.Rational(n) for n in raw_nums]
        n = len(data)
        if n == 0:
            raise ValueError("No numbers provided for statistical calculation.")

        mean_val = sum(data) / sp.Rational(n)
        sorted_data = sorted(data)
        if n % 2 == 1:
            median_val = sorted_data[n // 2]
        else:
            median_val = (sorted_data[n // 2 - 1] + sorted_data[n // 2]) / sp.Rational(2)

        # Sample variance s^2 = sum(x - mean)^2 / (n - 1)
        if n > 1:
            variance_val = sum((x - mean_val)**2 for x in data) / sp.Rational(n - 1)
            std_dev_val = sp.sqrt(variance_val)
        else:
            variance_val = sp.Integer(0)
            std_dev_val = sp.Integer(0)

        steps = [
            SolutionStep(
                step_number=1,
                title="Sample Size & Mean",
                explanation=f"Sample size $n = {n}$. Sum of values $\\sum x_i = {sp.latex(sum(data))}$. Calculate mean $\\mu = \\frac{{\\sum x_i}}{{n}}$.",
                math_expression=f"$$\\mu = \\frac{{{sp.latex(sum(data))}}}{{{n}}} = {sp.latex(mean_val)}$$"
            ),
            SolutionStep(
                step_number=2,
                title="Median",
                explanation="Sort observations in ascending order and find the central value.",
                math_expression=f"$$\\text{{Median}} = {sp.latex(median_val)}$$"
            ),
            SolutionStep(
                step_number=3,
                title="Variance & Standard Deviation",
                explanation=f"Sample variance $s^2 = \\frac{{\\sum (x_i - \\mu)^2}}{{n - 1}}$ and $s = \\sqrt{{s^2}}$.",
                math_expression=f"$$s^2 = {sp.latex(variance_val)}, \\quad s = {sp.latex(std_dev_val)} \\approx {float(std_dev_val):.3f}$$"
            )
        ]

        res_str = f"Mean={mean_val}, Median={median_val}, Variance={variance_val}, StdDev={float(std_dev_val):.3f}"
        latex_res = f"$$\\mu = {sp.latex(mean_val)}, \\quad s = {sp.latex(std_dev_val)}$$"

        return MathSolveResponse(
            expression=expr_str,
            operation="statistics",
            result=res_str,
            latex_result=latex_res,
            steps=steps,
            symbolic_verified=True,
            explanation=f"Dataset (n={n}) has Mean={mean_val}, Median={median_val}, Standard Deviation={float(std_dev_val):.3f}."
        )


sympy_solver = SymPyMathSolver()
