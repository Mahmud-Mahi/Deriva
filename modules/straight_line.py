from typing import Any

from sympy.geometry import Line, Ray, Segment

from formatter import indented_math
from models import MathTask


SYMPY_LOCALS = {
    "Line": Line,
    "Segment": Segment,
    "Ray": Ray,
}

RULES = [
    "For STRAIGHT-LINE: Use Line(Point(...), Point(...)) and call .equation() when the equation of the line is required.",
]

EXAMPLES = [
    'User problem: Line through (0,0) and (1,1)\nJSON: {"operation":"evaluate","expression":"Line(Point(0,0), Point(1,1)).equation()"}',
]


def execute(task: MathTask, expr, variables: list, equations: list):
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if "Line(" in expr_str and ".equation" in expr_str:
        lines = [
            "1. Identify the points or slope provided for the line.",
            "2. Use the point-slope form: y - y₁ = m(x - x₁).",
            "3. Simplify into the general form ax + by + c = 0.",
            "4. The line equation is:",
            indented_math(result),
        ]
        return "\n".join(lines)
    return None
