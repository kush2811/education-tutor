"""Curated ChatGPT-style STEM concept knowledge base with fuzzy spelling tolerance and diagram tags."""

import re
import difflib
from typing import Dict, Any, Optional, List
from app.schemas.tutor import SolutionStep


CONCEPT_KNOWLEDGE_BASE: Dict[str, Dict[str, Any]] = {
    "pythagoras theorem": {
        "title": "Pythagoras Theorem",
        "aliases": [
            "pythagoras", "pythagorean", "pyhtagoras", "pythagoros", "pythogoras",
            "pythagoras theorem", "pythagorean theorem", "right triangle theorem", "hypotenuse formula"
        ],
        "explanation": (
            "**Pythagoras' Theorem** states that in a **right-angled triangle**, the square of the hypotenuse is equal to the sum of the squares of the other two sides.\n\n"
            "### Formula\n\n"
            "$$c^2 = a^2 + b^2$$\n\n"
            "Where:\n"
            "- **a** = Base\n"
            "- **b** = Perpendicular (height)\n"
            "- **c** = Hypotenuse (longest side, opposite the $90^\\circ$ angle)\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "right_triangle\n"
            "```\n\n"
            "### Example\n"
            "Suppose a right-angled triangle has:\n"
            "- Base $a = 3$\n"
            "- Perpendicular $b = 4$\n\n"
            "Substitute into the formula:\n\n"
            "$$c^2 = 3^2 + 4^2 = 9 + 16 = 25$$\n\n"
            "$$c = \\sqrt{25} = 5$$\n\n"
            "So the length of the hypotenuse is **$5$**.\n\n"
            "Would you like to solve a specific triangle problem with this formula?"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Identify the Right Triangle Sides", explanation="Label the base (a), perpendicular (b), and longest side opposite the 90 degree angle as hypotenuse (c).", math_expression="a, b, c"),
            SolutionStep(step_number=2, title="Apply Pythagoras Formula", explanation="Sum the squares of the two legs to equal the square of the hypotenuse.", math_expression="c^2 = a^2 + b^2"),
            SolutionStep(step_number=3, title="Take the Square Root", explanation="Solve for the unknown side by taking the positive square root.", math_expression="c = \\sqrt{a^2 + b^2}")
        ],
        "final_answer": "c^2 = a^2 + b^2"
    },
    "trigonometry": {
        "title": "Trigonometric Ratios (SOH-CAH-TOA)",
        "aliases": ["trigonometry", "trigonometric", "trignometry", "sine cosine tangent", "sohcahtoa", "sin cos tan"],
        "explanation": (
            "**Trigonometry** studies the relationship between the angles and side lengths of triangles, starting with **right-angled triangles**.\n\n"
            "### Core Ratios (SOH-CAH-TOA)\n"
            "For an acute angle $\\theta$ in a right-angled triangle:\n\n"
            "$$\\sin(\\theta) = \\frac{\\text{Opposite}}{\\text{Hypotenuse}}, \\quad \\cos(\\theta) = \\frac{\\text{Adjacent}}{\\text{Hypotenuse}}, \\quad \\tan(\\theta) = \\frac{\\text{Opposite}}{\\text{Adjacent}}$$\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "right_triangle\n"
            "```\n\n"
            "### Fundamental Identity\n"
            "Using Pythagoras' theorem ($a^2 + b^2 = c^2$), dividing by $c^2$ yields the most important identity in trigonometry:\n\n"
            "$$\\sin^2(\\theta) + \\cos^2(\\theta) = 1$$\n\n"
            "### Example\n"
            "If a right triangle has an opposite side of $3$ and a hypotenuse of $5$:\n\n"
            "$$\\sin(\\theta) = \\frac{3}{5} = 0.6 \\implies \\theta = \\arcsin(0.6) \\approx 36.87^\\circ$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Reference Angle", explanation="Choose the acute angle theta and label Opposite, Adjacent, and Hypotenuse sides.", math_expression="\\theta"),
            SolutionStep(step_number=2, title="Apply SOH-CAH-TOA", explanation="Form the ratio corresponding to sine, cosine, or tangent.", math_expression="\\sin(\\theta) = \\frac{O}{H}, \\cos(\\theta) = \\frac{A}{H}, \\tan(\\theta) = \\frac{O}{A}")
        ],
        "final_answer": "\\sin(\\theta) = \\frac{\\text{Opposite}}{\\text{Hypotenuse}}"
    },
    "conditional probability": {
        "title": "Conditional Probability",
        "aliases": ["conditional probability", "conditonal probability", "probability given", "p(a|b)"],
        "explanation": (
            "**Conditional probability** is the probability of an event occurring given that another event has already taken place. We write it as $P(A|B)$, read as **\"the probability of A given B\"**.\n\n"
            "### Formula\n\n"
            "$$P(A|B) = \\frac{P(A \\cap B)}{P(B)}$$\n\n"
            "Where:\n"
            "- **$P(A|B)$** = Probability of event $A$ occurring given $B$ occurred\n"
            "- **$P(A \\cap B)$** = Probability that both events $A$ and $B$ occur together\n"
            "- **$P(B)$** = Probability of event $B$ (with $P(B) > 0$)\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "conditional_probability_venn\n"
            "```\n\n"
            "### Example (Rolling a Die)\n"
            "Imagine rolling a fair 6-sided die:\n"
            "- Normally, the chance of rolling a $2$ is $\\frac{1}{6}$ across $\\{1, 2, 3, 4, 5, 6\\}$.\n"
            "- Suppose you are told: *\"The roll is an even number.\"* Now the sample space shrinks to $\\{2, 4, 6\\}$.\n"
            "- Only one of those three outcomes is a $2$, so:\n\n"
            "$$P(\\text{Roll 2} \\mid \\text{Even}) = \\frac{1/6}{3/6} = \\frac{1}{3}$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Restrict Sample Space", explanation="Narrow all possible outcomes to only those inside event B.", math_expression="S \\to B"),
            SolutionStep(step_number=2, title="Apply Formula", explanation="Divide the probability of the overlap P(A and B) by P(B).", math_expression="P(A|B) = \\frac{P(A \\cap B)}{P(B)}")
        ],
        "final_answer": "P(A|B) = \\frac{P(A \\cap B)}{P(B)}"
    },
    "bayes theorem": {
        "title": "Bayes' Theorem",
        "aliases": ["bayes theorem", "bayes rule", "bayes", "posterior probability"],
        "explanation": (
            "**Bayes' Theorem** provides a mathematical rule to update the probability of a hypothesis when new evidence becomes available.\n\n"
            "### Formula\n\n"
            "$$P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}$$\n\n"
            "Where:\n"
            "- **$P(A|B)$** = Posterior probability (updated probability of $A$ given evidence $B$)\n"
            "- **$P(B|A)$** = Likelihood of observing evidence $B$ if $A$ is true\n"
            "- **$P(A)$** = Prior probability of $A$ before seeing evidence\n"
            "- **$P(B)$** = Total probability of observing evidence $B$\n\n"
            "### Example\n"
            "In medical testing, if a rare condition affects $1\\%$ of people ($P(A) = 0.01$) and a test has $99\\%$ sensitivity and $5\\%$ false positive rate, Bayes' Theorem prevents overestimating disease risk from a single positive result."
        ),
        "steps": [
            SolutionStep(step_number=1, title="State Prior and Likelihood", explanation="Identify P(A) and P(B|A).", math_expression="P(A), P(B|A)"),
            SolutionStep(step_number=2, title="Compute Posterior", explanation="Multiply prior by likelihood and divide by evidence probability P(B).", math_expression="P(A|B) = \\frac{P(B|A)P(A)}{P(B)}")
        ],
        "final_answer": "P(A|B) = \\frac{P(B|A) \\cdot P(A)}{P(B)}"
    },
    "quadratic equation": {
        "title": "Quadratic Equations & Quadratic Formula",
        "aliases": ["quadratic equation", "quadratic formula", "roots of ax^2", "discriminant", "parabola"],
        "explanation": (
            "A **quadratic equation** is a second-degree polynomial equation in a single variable $x$.\n\n"
            "### Standard Form & Quadratic Formula\n\n"
            "$$ax^2 + bx + c = 0 \\quad (a \\neq 0)$$\n\n"
            "The roots (solutions) for $x$ are given by the **Quadratic Formula**:\n\n"
            "$$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$\n\n"
            "Where:\n"
            "- **$a, b, c$** = Real numerical coefficients\n"
            "- **$\\Delta = b^2 - 4ac$** = The **Discriminant**, which tells us the nature of the roots:\n"
            "  - $\\Delta > 0$: Two distinct real roots\n"
            "  - $\\Delta = 0$: One repeated real root\n"
            "  - $\\Delta < 0$: Two **complex / imaginary** conjugate roots ($x = \\frac{-b \\pm i\\sqrt{4ac - b^2}}{2a}$)\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "quadratic_parabola\n"
            "```\n\n"
            "### Example\n"
            "For $x^2 - 5x + 6 = 0$ ($a = 1, b = -5, c = 6$):\n\n"
            "$$x = \\frac{5 \\pm \\sqrt{(-5)^2 - 4(1)(6)}}{2(1)} = \\frac{5 \\pm 1}{2} \\implies x = 3 \\text{ or } x = 2$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Identify Coefficients", explanation="Extract a, b, and c from ax^2 + bx + c = 0.", math_expression="a, b, c"),
            SolutionStep(step_number=2, title="Apply Quadratic Formula", explanation="Compute discriminant b^2 - 4ac and solve for x.", math_expression="x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}")
        ],
        "final_answer": "x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}"
    },
    "derivative": {
        "title": "Derivatives in Calculus",
        "aliases": ["derivative", "differentiation", "derivate", "rate of change", "tangent slope"],
        "explanation": (
            "A **derivative** measures the **instantaneous rate of change** of a function with respect to a variable. Geometrically, it represents the **slope of the tangent line** to a curve at any point.\n\n"
            "### Formula (Limit Definition)\n\n"
            "$$f'(x) = \\frac{df}{dx} = \\lim_{h \\to 0} \\frac{f(x + h) - f(x)}{h}$$\n\n"
            "### Essential Differentiation Rules\n"
            "- **Power Rule:** $\\frac{d}{dx}(x^n) = n x^{n-1}$\n"
            "- **Constant Rule:** $\\frac{d}{dx}(c) = 0$\n"
            "- **Product Rule:** $(uv)' = u'v + uv'$\n"
            "- **Chain Rule:** $\\frac{d}{dx} f(g(x)) = f'(g(x)) \\cdot g'(x)$\n\n"
            "### Example\n"
            "Find the derivative of $f(x) = x^3 - 4x + 7$:\n\n"
            "$$f'(x) = 3x^2 - 4$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Difference Quotient", explanation="Measure average slope across interval h.", math_expression="\\frac{f(x+h) - f(x)}{h}"),
            SolutionStep(step_number=2, title="Take Limit as h -> 0", explanation="Shrink h to zero for instantaneous slope.", math_expression="f'(x) = \\lim_{h \\to 0} \\frac{f(x+h)-f(x)}{h}")
        ],
        "final_answer": "f'(x) = \\lim_{h \\to 0} \\frac{f(x + h) - f(x)}{h}"
    },
    "integral": {
        "title": "Integrals in Calculus",
        "aliases": ["integral", "integration", "antiderivative", "area under curve"],
        "explanation": (
            "An **integral** represents the **accumulation of quantities**—most commonly visualized as the **area under a curve** on a graph.\n\n"
            "### Formulas\n"
            "- **Indefinite Integral (Antiderivative):**\n\n"
            "$$\\int f(x)\\,dx = F(x) + C$$\n\n"
            "- **Definite Integral (Area from $a$ to $b$):**\n\n"
            "$$\\int_{a}^{b} f(x)\\,dx = F(b) - F(a)$$\n\n"
            "Where $F'(x) = f(x)$ (by the Fundamental Theorem of Calculus) and $C$ is the constant of integration.\n\n"
            "### Example\n"
            "Find the area under $f(x) = 3x^2$ from $x = 0$ to $x = 2$:\n\n"
            "$$\\int_{0}^{2} 3x^2\\,dx = \\left[x^3\\right]_{0}^{2} = 2^3 - 0^3 = 8$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Find Antiderivative", explanation="Reverse differentiation to find F(x).", math_expression="F(x) = \\int f(x)\\,dx"),
            SolutionStep(step_number=2, title="Apply Bounds", explanation="Evaluate F(b) - F(a) for definite integrals.", math_expression="F(b) - F(a)")
        ],
        "final_answer": "\\int_{a}^{b} f(x)\\,dx = F(b) - F(a)"
    },
    "newton": {
        "title": "Newton's Laws of Motion",
        "aliases": ["newton", "newtons law", "newton's law", "laws of motion", "inertia", "f=ma", "second law"],
        "explanation": (
            "**Newton's Three Laws of Motion** explain how forces affect the motion of physical objects.\n\n"
            "### 1. First Law (Law of Inertia)\n"
            "An object at rest stays at rest, and an object in motion keeps moving at constant velocity, unless acted upon by an unbalanced net external force.\n\n"
            "### 2. Second Law (Force & Acceleration)\n"
            "Force equals mass multiplied by acceleration:\n\n"
            "$$\\mathbf{F} = m \\mathbf{a}$$\n\n"
            "Where:\n"
            "- **$\\mathbf{F}$** = Net force in Newtons ($\\text{N}$)\n"
            "- **$m$** = Mass in kilograms ($\\text{kg}$)\n"
            "- **$\\mathbf{a}$** = Acceleration in $\\text{m/s}^2$\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "force_acceleration\n"
            "```\n\n"
            "### 3. Third Law (Action & Reaction)\n"
            "For every action force, there is an equal and opposite reaction force ($\\mathbf{F}_{AB} = -\\mathbf{F}_{BA}$).\n\n"
            "### Example\n"
            "If a $5\\text{ kg}$ box is pushed with a net force of $20\\text{ N}$, its acceleration is:\n\n"
            "$$a = \\frac{F}{m} = \\frac{20}{5} = 4\\text{ m/s}^2$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="First Law (Inertia)", explanation="Zero net force means zero acceleration.", math_expression="\\sum F = 0"),
            SolutionStep(step_number=2, title="Second Law", explanation="Acceleration is proportional to net force and inversely proportional to mass.", math_expression="F = ma")
        ],
        "final_answer": "F = m \\cdot a"
    },
    "ohms law": {
        "title": "Ohm's Law",
        "aliases": ["ohm", "ohms law", "ohm's law", "voltage current resistance", "v=ir"],
        "explanation": (
            "**Ohm's Law** states that the electric current flowing through a conductor between two points is directly proportional to the voltage across it and inversely proportional to its resistance.\n\n"
            "### Formula\n\n"
            "$$V = I \\cdot R$$\n\n"
            "Where:\n"
            "- **$V$** = Voltage (Potential difference) in Volts ($\\text{V}$)\n"
            "- **$I$** = Current in Amperes ($\\text{A}$)\n"
            "- **$R$** = Resistance in Ohms ($\\Omega$)\n\n"
            "### Diagram\n\n"
            "```diagram\n"
            "ohms_law_circuit\n"
            "```\n\n"
            "### Example\n"
            "If a $12\\text{ V}$ battery is connected across a $4\\,\\Omega$ resistor, the current flowing through the circuit is:\n\n"
            "$$I = \\frac{V}{R} = \\frac{12}{4} = 3\\text{ A}$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Identify Circuit Parameters", explanation="Determine Voltage (V), Current (I), and Resistance (R).", math_expression="V, I, R"),
            SolutionStep(step_number=2, title="Apply Ohm's Law", explanation="Use V = I * R to solve for the unknown quantity.", math_expression="V = I \\cdot R")
        ],
        "final_answer": "V = I \\cdot R"
    },
    "electromagnetic induction": {
        "title": "Electromagnetic Induction (Faraday's Law)",
        "aliases": ["electromagnetic induction", "faraday", "faraday's law", "lenz", "induced emf"],
        "explanation": (
            "**Electromagnetic induction** is the process of generating an electric voltage (EMF) and current in a conductor by changing the magnetic field around it.\n\n"
            "### Faraday's Law Formula\n\n"
            "$$\\mathcal{E} = -N \\frac{d\\Phi_B}{dt}$$\n\n"
            "Where:\n"
            "- **$\\mathcal{E}$** = Induced electromotive force (voltage in Volts)\n"
            "- **$N$** = Number of turns in the coil\n"
            "- **$\\frac{d\\Phi_B}{dt}$** = Rate of change of magnetic flux through the loop\n"
            "- The negative sign comes from **Lenz's Law** (conservation of energy): the induced current always opposes the change that created it.\n\n"
            "### Real-World Intuition\n"
            "Moving a magnet rapidly back and forth inside a copper coil changes the magnetic field lines passing through the loop, pushing electrons around the wire to produce electricity—this is how generators and wind turbines work."
        ),
        "steps": [
            SolutionStep(step_number=1, title="Magnetic Flux", explanation="Measure magnetic field passing through area A.", math_expression="\\Phi_B = B \\cdot A \\cos\\theta"),
            SolutionStep(step_number=2, title="Induced EMF", explanation="Changing flux over time induces voltage proportional to coil turns N.", math_expression="\\mathcal{E} = -N \\frac{d\\Phi_B}{dt}")
        ],
        "final_answer": "\\mathcal{E} = -N \\frac{d\\Phi_B}{dt}"
    },
    "photosynthesis": {
        "title": "Photosynthesis",
        "aliases": ["photosynthesis", "photoynthesis", "chloroplast", "chlorophyll"],
        "explanation": (
            "**Photosynthesis** is the biochemical process by which green plants, algae, and certain bacteria convert light energy from the sun into chemical energy stored in glucose.\n\n"
            "### Balanced Chemical Equation\n\n"
            "$$6\\text{CO}_2 + 6\\text{H}_2\\text{O} + \\text{Light Energy} \\longrightarrow \\text{C}_6\\text{H}_{12}\\text{O}_6 + 6\\text{O}_2$$\n\n"
            "Where:\n"
            "- **Inputs:** Carbon dioxide ($\\text{CO}_2$) from air, water ($\\text{H}_2\\text{O}$) from roots, and sunlight absorbed by chlorophyll inside **chloroplasts**.\n"
            "- **Outputs:** Glucose ($\\text{C}_6\\text{H}_{12}\\text{O}_6$) for plant energy and oxygen gas ($\\text{O}_2$) released into the atmosphere.\n\n"
            "### Two Main Stages\n"
            "1. **Light-Dependent Reactions (Thylakoid membranes):** Capture sunlight to split water, release $\\text{O}_2$, and generate energy carriers ($\\text{ATP}$ and $\\text{NADPH}$).\n"
            "2. **Calvin Cycle / Light-Independent Reactions (Stroma):** Use $\\text{ATP}$ and $\\text{NADPH}$ to fix $\\text{CO}_2$ into glucose sugars."
        ),
        "steps": [
            SolutionStep(step_number=1, title="Light Reactions", explanation="Absorb photons to produce ATP, NADPH, and oxygen.", math_expression="2H_2O \\to O_2 + 4H^+ + 4e^-"),
            SolutionStep(step_number=2, title="Calvin Cycle", explanation="Fix CO2 into glucose using ATP and NADPH.", math_expression="6CO_2 \\to C_6H_{12}O_6")
        ],
        "final_answer": "6CO_2 + 6H_2O + \\text{Light} \\to C_6H_{12}O_6 + 6O_2"
    },
    "big o notation": {
        "title": "Big-O Notation & Time Complexity",
        "aliases": ["big o", "big-o", "time complexity", "asymptotic analysis", "space complexity"],
        "explanation": (
            "**Big-O notation** describes how the runtime or memory usage of an algorithm grows as the input size $n$ becomes large.\n\n"
            "### Common Complexity Classes (Fastest to Slowest)\n"
            "| Notation | Name | Example |\n"
            "| :--- | :--- | :--- |\n"
            "| $O(1)$ | Constant | Array element lookup by index (`arr[5]`) |\n"
            "| $O(\\log n)$ | Logarithmic | Binary search in a sorted list |\n"
            "| $O(n)$ | Linear | Finding the max element in an unsorted list |\n"
            "| $O(n \\log n)$ | Linearithmic | Merge Sort, Quick Sort (average) |\n"
            "| $O(n^2)$ | Quadratic | Nested loops (Bubble Sort, checking all pairs) |\n\n"
            "### Example\n"
            "Searching a sorted list of $1,000,000$ items:\n"
            "- **Linear search ($O(n)$):** Up to $1,000,000$ checks.\n"
            "- **Binary search ($O(\\log n)$):** Only about $20$ checks, because the search space halves each step."
        ),
        "steps": [
            SolutionStep(step_number=1, title="Count Operations vs Input n", explanation="Express steps as a function T(n) of input size n.", math_expression="T(n)"),
            SolutionStep(step_number=2, title="Keep Dominant Term", explanation="Drop constants and lower-order terms to isolate asymptotic growth.", math_expression="O(g(n))")
        ],
        "final_answer": "O(1) < O(\\log n) < O(n) < O(n \\log n) < O(n^2)"
    },
    "recursion": {
        "title": "Recursion in Computer Science",
        "aliases": ["recursion", "recursive function", "base case"],
        "explanation": (
            "**Recursion** is a programming technique where a function solves a problem by **calling itself** on a smaller sub-problem until it reaches a stopping condition.\n\n"
            "### Two Essential Parts\n"
            "1. **Base Case:** The simplest case that returns an answer directly without recursing (prevents infinite loops / stack overflow).\n"
            "2. **Recursive Case:** Reduces the current problem toward the base case.\n\n"
            "### Example (Factorial in Python)\n"
            "Since $n! = n \\times (n-1)!$ and $0! = 1$:\n\n"
            "```python\n"
            "def factorial(n):\n"
            "    if n <= 1:        # Base case\n"
            "        return 1\n"
            "    return n * factorial(n - 1)  # Recursive step\n"
            "```"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Define Base Case", explanation="Establish stopping condition.", math_expression="n \\le 1 \\implies 1"),
            SolutionStep(step_number=2, title="Define Recursive Step", explanation="Break down problem into smaller sub-call.", math_expression="f(n) = n \\cdot f(n-1)")
        ],
        "final_answer": "n! = n \\times (n - 1)!"
    },
    "kinematics": {
        "title": "Equations of Kinematics (Constant Acceleration)",
        "aliases": ["kinematics", "equations of motion", "velocity acceleration", "suvat", "projectile"],
        "explanation": (
            "**Kinematics** describes the motion of objects (position, velocity, and acceleration) without focusing on the forces causing it.\n\n"
            "### Three Core Equations (Constant Acceleration $a$)\n\n"
            "1. $v = u + at$\n"
            "2. $s = ut + \\frac{1}{2}at^2$\n"
            "3. $v^2 = u^2 + 2as$\n\n"
            "Where:\n"
            "- **$u$** = Initial velocity ($\\text{m/s}$)\n"
            "- **$v$** = Final velocity ($\\text{m/s}$)\n"
            "- **$a$** = Constant acceleration ($\\text{m/s}^2$)\n"
            "- **$t$** = Time elapsed ($\\text{s}$)\n"
            "- **$s$** = Displacement ($\\text{m}$)\n\n"
            "### Example\n"
            "A car starts from rest ($u = 0$) and accelerates at $3\\text{ m/s}^2$ for $4\\text{ s}$:\n\n"
            "$$v = 0 + (3)(4) = 12\\text{ m/s}$$\n"
            "$$s = 0 + \\frac{1}{2}(3)(4^2) = 24\\text{ m}$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="List Knowns (SUVAT)", explanation="Identify u, v, a, t, and s.", math_expression="u, v, a, t, s"),
            SolutionStep(step_number=2, title="Select Equation", explanation="Pick the equation relating known variables to the unknown.", math_expression="s = ut + \\frac{1}{2}at^2")
        ],
        "final_answer": "v = u + at, \\quad s = ut + \\frac{1}{2}at^2, \\quad v^2 = u^2 + 2as"
    },
    "probability": {
        "title": "Probability Fundamentals",
        "aliases": ["what is probability", "probability formula", "basic probability", "sample space"],
        "explanation": (
            "**Probability** measures how likely an event is to occur, expressed as a number between **$0$** (impossible) and **$1$** (certain), or $0\\%$ to $100\\%$.\n\n"
            "### Formula\n\n"
            "$$P(E) = \\frac{\\text{Number of favorable outcomes}}{\\text{Total number of equally likely outcomes}}$$\n\n"
            "### Key Rules\n"
            "- **Range:** $0 \\le P(E) \\le 1$\n"
            "- **Complement Rule:** $P(\\text{not } E) = 1 - P(E)$\n"
            "- **Addition Rule:** $P(A \\cup B) = P(A) + P(B) - P(A \\cap B)$\n\n"
            "### Example\n"
            "Drawing an Ace from a standard 52-card deck: there are $4$ Aces out of $52$ cards:\n\n"
            "$$P(\\text{Ace}) = \\frac{4}{52} = \\frac{1}{13} \\approx 7.69\\%$$"
        ),
        "steps": [
            SolutionStep(step_number=1, title="Count Sample Space", explanation="Find total possible outcomes.", math_expression="n(S)"),
            SolutionStep(step_number=2, title="Compute Ratio", explanation="Divide favorable outcomes by total outcomes.", math_expression="P(E) = \\frac{n(E)}{n(S)}")
        ],
        "final_answer": "P(E) = \\frac{n(E)}{n(S)}"
    }
}


def find_best_concept(query: str) -> Optional[Dict[str, Any]]:
    """Find best matching concept using exact alias search followed by fuzzy spelling tolerance."""
    q_clean = re.sub(r'[^a-z0-9\s\^\=]', ' ', query.lower()).strip()
    q_clean = re.sub(r'\s+', ' ', q_clean)

    # 1. Exact key or alias substring match (longest match wins so 'conditional probability' beats 'probability')
    best_key = None
    best_len = 0
    for key, data in CONCEPT_KNOWLEDGE_BASE.items():
        candidates = [key] + data.get("aliases", [])
        for alias in candidates:
            if alias in q_clean and len(alias) > best_len:
                best_key = key
                best_len = len(alias)
    if best_key:
        return CONCEPT_KNOWLEDGE_BASE[best_key]

    # 2. Fuzzy word/phrase match for typos (e.g., "pyhtagoras theorem" -> "pythagoras theorem")
    stripped_q = re.sub(r'^(what is|what are|define|explain|tell me about|how does|why does)\s+', '', q_clean).strip()
    all_aliases: Dict[str, str] = {}
    for key, data in CONCEPT_KNOWLEDGE_BASE.items():
        all_aliases[key] = key
        for alias in data.get("aliases", []):
            all_aliases[alias] = key

    close_phrase = difflib.get_close_matches(stripped_q, list(all_aliases.keys()), n=1, cutoff=0.72)
    if close_phrase:
        return CONCEPT_KNOWLEDGE_BASE[all_aliases[close_phrase[0]]]

    # Token-level fuzzy match against significant words
    for word in stripped_q.split():
        if len(word) >= 5:
            close_word = difflib.get_close_matches(word, list(all_aliases.keys()), n=1, cutoff=0.78)
            if close_word:
                return CONCEPT_KNOWLEDGE_BASE[all_aliases[close_word[0]]]

    return None

