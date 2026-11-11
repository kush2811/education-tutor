"""Speech normalizer: converts structured academic markdown, mathematical LaTeX, code blocks, and tables into natural spoken English."""

import re
from typing import List, Tuple, Dict, Any


class EducationalSpeechNormalizer:
    """Transforms structured educational answers (LaTeX formulas, code blocks, markdown tables,

    headings, and citations) into clear, natural, spoken conversational scripts for TTS.
    """

    def __init__(self):
        # Common Greek symbols in STEM
        self._greek_symbols = {
            r'\\alpha': 'alpha',
            r'\\beta': 'beta',
            r'\\gamma': 'gamma',
            r'\\delta': 'delta',
            r'\\Delta': 'delta',
            r'\\epsilon': 'epsilon',
            r'\\zeta': 'zeta',
            r'\\eta': 'eta',
            r'\\theta': 'theta',
            r'\\lambda': 'lambda',
            r'\\mu': 'mu',
            r'\\nu': 'nu',
            r'\\xi': 'xi',
            r'\\pi': 'pi',
            r'\\rho': 'rho',
            r'\\sigma': 'sigma',
            r'\\Sigma': 'sigma',
            r'\\tau': 'tau',
            r'\\phi': 'phi',
            r'\\chi': 'chi',
            r'\\psi': 'psi',
            r'\\omega': 'omega',
            r'\\Omega': 'omega',
        }

        # LaTeX mathematical operators & relations
        self._math_operators = [
            (r'\\frac\{d\}\{dx\}', 'the derivative with respect to x of'),
            (r'\\frac\{\\partial\}\{\\partial\s*x\}', 'the partial derivative with respect to x of'),
            (r'\\leq|\\le', 'is less than or equal to'),
            (r'\\geq|\\ge', 'is greater than or equal to'),
            (r'\\neq', 'is not equal to'),
            (r'\\approx', 'is approximately equal to'),
            (r'\\times', 'times'),
            (r'\\cdot', 'times'),
            (r'\^\s*\\circ|\\circ', ' degrees'),
            (r'\\pm', 'plus or minus'),
            (r'\\mp', 'minus or plus'),
            (r'\\implies', 'implies that'),
            (r'\\iff', 'if and only if'),
            (r'\\infty', 'infinity'),
            (r'\\in', 'is an element of'),
            (r'\\notin', 'is not in'),
            (r'\\to|\\rightarrow', 'approaches'),
            (r'\\forall', 'for all'),
            (r'\\exists', 'there exists'),
        ]

    def normalize_math(self, text: str) -> str:
        """Convert LaTeX equations and math symbols into natural spoken English."""
        # 1. Limits: \lim_{x \to 0} or \lim_{x \rightarrow a}
        text = re.sub(
            r'\\lim_\{([a-zA-Z])\s*\\(?:to|rightarrow)\s*([^}]+)\}',
            r'the limit as \1 approaches \2 of ',
            text
        )

        # 2. Definite & Indefinite Integrals: \int_{a}^{b} f(x) dx or \int f(x) dx
        text = re.sub(
            r'\\int_\{([^}]+)\}\^\{([^}]+)\}',
            r'the integral from \1 to \2 of ',
            text
        )
        text = re.sub(r'\\int', 'the integral of ', text)

        # 3. Summations: \sum_{i=1}^{n}
        text = re.sub(
            r'\\sum_\{([^}]+)\}\^\{([^}]+)\}',
            r'the summation from \1 to \2 of ',
            text
        )
        text = re.sub(r'\\sum', 'the sum of ', text)

        # 4. Derivatives: \frac{df}{dx} or \frac{dy}{dx}
        text = re.sub(
            r'\\frac\{d([a-zA-Z])\}\{d([a-zA-Z])\}',
            r'the derivative of \1 with respect to \2 ',
            text
        )

        # 5. Fractions: \frac{numerator}{denominator}
        # Nested or single fractions
        while r'\frac{' in text:
            text = re.sub(r'\\frac\{([^{}]+)\}\{([^{}]+)\}', r'\1 over \2', text)

        # 6. Roots: \sqrt[n]{x} and \sqrt{x}
        text = re.sub(r'\\sqrt\[([^\]]+)\]\{([^{}]+)\}', r'the \1 root of \2', text)
        text = re.sub(r'\\sqrt\{([^{}]+)\}', r'the square root of \1', text)

        # 7. Powers: x^2, x^3, x^{expression}
        text = re.sub(r'([a-zA-Z0-9)\]])\^2\b', r'\1 squared', text)
        text = re.sub(r'([a-zA-Z0-9)\]])\^3\b', r'\1 cubed', text)
        text = re.sub(r'([a-zA-Z0-9)\]])\^\{([^}]+)\}', r'\1 to the power of \2', text)
        text = re.sub(r'([a-zA-Z0-9)\]])\^([a-zA-Z0-9])', r'\1 to the power of \2', text)

        # 8. Subscripts: x_1, x_{max}
        text = re.sub(r'([a-zA-Z])_\{([^}]+)\}', r'\1 sub \2', text)
        text = re.sub(r'([a-zA-Z])_([0-9a-zA-Z])', r'\1 sub \2', text)

        # 9. Greek Symbols
        for pat, replacement in self._greek_symbols.items():
            text = re.sub(pat, replacement, text)

        # 10. Operators and Relations
        for pat, replacement in self._math_operators:
            text = re.sub(pat, f" {replacement} ", text)

        # 11. Equal signs and arithmetic symbols in formulas
        text = re.sub(r'([a-zA-Z0-9])\s*=\s*', r'\1 equals ', text)
        text = re.sub(r'\s*\+\s*', ' plus ', text)
        text = re.sub(r'\s*-\s*', ' minus ', text)
        text = re.sub(r'\s*\*\s*', ' times ', text)
        text = re.sub(r'\s*/\s*', ' divided by ', text)

        # 12. Implicit multiplication between variables (e.g. ma -> m times a, mc -> m times c, 2x -> 2 times x)
        common_two_letter_words = {
            'of', 'to', 'in', 'is', 'as', 'at', 'on', 'by', 'if', 'or', 'we',
            'an', 'am', 'no', 'so', 'do', 'go', 'me', 'my', 'up', 'us', 'he',
            'it', 'pi', 'mu', 'nu', 'xi', 'dx', 'dy', 'dt', 'dr', 'dz', 'ds', 'df'
        }

        def _split_mult(m: re.Match) -> str:
            word = m.group(0)
            if word.lower() in common_two_letter_words:
                return word
            return f"{m.group(1)} times {m.group(2)}"

        text = re.sub(r'\b([a-zA-Z])([a-zA-Z])\b', _split_mult, text)
        text = re.sub(r'\b([a-zA-Z])([a-zA-Z])\s+squared', r'\1 times \2 squared', text)
        text = re.sub(r'\b([a-zA-Z])([a-zA-Z])\s+cubed', r'\1 times \2 cubed', text)
        text = re.sub(r'\b([0-9]+)([a-zA-Z])\b', r'\1 times \2', text)

        # Clean remaining LaTeX command slashes and braces
        text = re.sub(r'\\[a-zA-Z]+', '', text)
        text = text.replace('{', '').replace('}', '')
        text = text.replace('$$', '').replace('$', '')

        return text

    def normalize_code_blocks(self, text: str) -> str:
        """Summarize programming code blocks and diagram blocks in plain English rather than reciting syntax."""
        code_block_pattern = re.compile(r'```([a-zA-Z0-9_]+)?\n(.*?)```', re.DOTALL)

        def replace_code(match: re.Match) -> str:
            lang = (match.group(1) or "").strip().lower()
            code = match.group(2).strip()
            if lang == "diagram":
                diagram_name = code.replace('_', ' ')
                return f" Refer to the {diagram_name} diagram shown on screen. "

            func_match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', code)
            class_match = re.search(r'class\s+([a-zA-Z0-9_]+)', code)

            if func_match:
                func_name = func_match.group(1).replace('_', ' ')
                return f" Here is a Python code implementation defining the function {func_name} to execute this logic. "
            elif class_match:
                class_name = class_match.group(1)
                return f" Here is a code implementation defining the class {class_name}. "
            else:
                lines = [l.strip() for l in code.split('\n') if l.strip()]
                return f" Here is a code example with {len(lines)} lines of logic demonstrating this solution. "

        return code_block_pattern.sub(replace_code, text)

    def normalize_tables(self, text: str) -> str:
        """Convert markdown tables into natural spoken sentences."""
        lines = text.split('\n')
        out_lines = []
        table_rows = []
        in_table = False

        for line in lines:
            line_str = line.strip()
            if line_str.startswith('|') and line_str.endswith('|'):
                in_table = True
                # Skip divider rows like |---|---|
                if re.match(r'^\|[\s\-:|]+\|$', line_str):
                    continue
                cells = [c.strip() for c in line_str.split('|')[1:-1]]
                table_rows.append(cells)
            else:
                if in_table and table_rows:
                    # Flush table as spoken text
                    headers = table_rows[0]
                    for r_idx, row in enumerate(table_rows[1:], start=1):
                        cell_pairs = [f"{headers[c]} is {row[c]}" for c in range(min(len(headers), len(row)))]
                        out_lines.append(f"Row {r_idx}: {', '.join(cell_pairs)}.")
                    table_rows = []
                    in_table = False
                out_lines.append(line)

        if in_table and table_rows:
            headers = table_rows[0]
            for r_idx, row in enumerate(table_rows[1:], start=1):
                cell_pairs = [f"{headers[c]} is {row[c]}" for c in range(min(len(headers), len(row)))]
                out_lines.append(f"Row {r_idx}: {', '.join(cell_pairs)}.")

        return '\n'.join(out_lines)

    def normalize_structured_text(self, markdown_text: str) -> str:
        """Convert complete structured markdown document into a continuous spoken script."""
        # 1. Replace code blocks
        text = self.normalize_code_blocks(markdown_text)

        # 2. Replace markdown tables
        text = self.normalize_tables(text)

        # 3. Strip footnote citation brackets [1], [2], [1 (Unverified Citation)]
        text = re.sub(r'\[\d+(?:\s*\([^)]*\))?\]', '', text)

        # 4. Normalize LaTeX math blocks $$...$$ and inline $...$
        text = re.sub(r'\$\$([\s\S]*?)\$\$', lambda m: self.normalize_math(m.group(1)), text)
        text = re.sub(r'\$([^\$]+?)\$', lambda m: self.normalize_math(m.group(1)), text)

        # 5. Clean markdown headers (#, ##, ###)
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        # 6. Clean bullet and list markers
        text = re.sub(r'^\s*[\*\-]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)

        # 7. Clean callout blockquotes
        text = re.sub(r'^>\s*\[!.*?\]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

        # 8. Clean inline markdown formatting (**bold**, *italic*, `code`)
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^*]+)\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # 8b. Normalize any remaining standalone '=' signs into 'equals'
        text = re.sub(r'\s*=\s*', ' equals ', text)

        # 9. Clean audit notice headers if present at the bottom
        text = re.sub(r'---\s*\n###?\s*🛡️ Answer Verification.*$', '', text, flags=re.DOTALL)

        # 10. Normalize whitespace and sentence punctuation
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def split_into_sentence_pairs(self, original_text: str) -> List[Tuple[str, str]]:
        """
        Split original markdown into display sentences, and pair each with its spoken normalized version.
        
        Returns:
            List of (display_text_sentence, spoken_text_sentence)
        """
        # Pre-collapse multi-line code and diagram blocks before splitting on newlines
        preprocessed = self.normalize_code_blocks(original_text)
        raw_lines = preprocessed.split('\n')
        pairs: List[Tuple[str, str]] = []

        for line in raw_lines:
            line = line.strip()
            if not line or line.startswith('---'):
                continue

            # Split line into sentences
            sub_sentences = re.split(r'(?<=[.!?])\s+', line)
            for sub in sub_sentences:
                sub = sub.strip()
                if not sub:
                    continue

                spoken = self.normalize_structured_text(sub)
                if spoken and len(spoken.split()) >= 1:
                    # Ensure ends with sentence punctuation
                    if not spoken.endswith(('.', '!', '?')):
                        spoken += '.'
                    pairs.append((sub, spoken))

        return pairs


speech_normalizer = EducationalSpeechNormalizer()
