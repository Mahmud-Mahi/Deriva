from typing import Any

from sympy.geometry import Plane, Point, Point3D, intersection

from formatter import indented_math
from models import MathTask


def geom_distance(obj1, obj2):
    return obj1.distance(obj2)


SYMPY_LOCALS = {
    "Point": Point,
    "Point3D": Point3D,
    "Plane": Plane,
    "intersection": intersection,
    "distance": geom_distance,
}

RULES = [
    "For 3D GEOMETRY: Use Plane(Point3D(...), normal_vector). Find distances with distance(Point, Plane).",
]

EXAMPLES = [
    'User problem: Distance from (1,2) to line 3x + 4y = 5\nJSON: {"operation":"evaluate","expression":"distance(Point(1, 2), Line(3*x + 4*y - 5))"}',
]


def execute(task: MathTask, expr, variables: list, equations: list):
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if "distance(" in expr_str:
        lines = [
            "1. Identify the geometric entities (Point, Line, or Plane).",
            "2. Apply the perpendicular distance formula.",
            "3. The calculated distance is:",
            indented_math(result),
        ]
        return "\n".join(lines)
    return None
