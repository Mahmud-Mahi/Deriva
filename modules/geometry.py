import sympy as sp
from sympy.geometry import (
    Point, Point3D, Line, Plane, Segment, Ray, Circle, 
    Ellipse, Parabola, intersection
)
from typing import Any
from models import MathTask
from formatter import indented_math, pretty_math, parse_math

def geom_distance(obj1, obj2):
    return obj1.distance(obj2)

SYMPY_LOCALS = {
    "Point": Point, "Point3D": Point3D, "Line": Line, "Plane": Plane, "Segment": Segment,
    "Ray": Ray, "Circle": Circle, "Ellipse": Ellipse, "Parabola": Parabola, "intersection": intersection, "distance": geom_distance
}

RULES = [
    "For 3D GEOMETRY: Use Plane(Point3D(...), normal_vector). Find distances with distance(Point, Plane).",
    "For CONICS: Use Parabola(focus, directrix), Ellipse(focus1, focus2, eccentricity/major_axis), or Hyperbola(focus1, focus2, major_axis)."
]

EXAMPLES = [
    'User problem: Distance from (1,2) to line 3x + 4y = 5\nJSON: {"operation":"evaluate","expression":"distance(Point(1, 2), Line(3*x + 4*y - 5))"}',
    'User problem: Line through (0,0) and (1,1)\nJSON: {"operation":"evaluate","expression":"Line(Point(0,0), Point(1,1)).equation()"}'
]

def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    # Specialized Case: Circle tangent to coordinate lines (from original script)
    if task.operation == "circle_tangent_coordinate_lines":
        x, y, a = sp.symbols("x y a")
        return [
            sp.Eq((2 * x - a) ** 2 + (2 * y - a) ** 2, a**2, evaluate=False),
            sp.Eq((2 * x - a) ** 2 + (2 * y + a) ** 2, a**2, evaluate=False),
        ]
    
    # General Evaluation for Geometry objects
    if task.operation == "evaluate":
        try:
            # Handle .equation() calls or property access
            return sp.simplify(expr)
        except:
            return expr
            
    return None

def get_steps(task: MathTask, expr_str: str, result: Any):
    lines = []
    
    # 1. Circle Tangent Case
    if task.operation == "circle_tangent_coordinate_lines":
        x, y, a = sp.symbols("x y a")
        lines.extend([
            "1. A circle tangent to x=0 and x=a has its center at x=a/2.",
            "2. The radius must be a/2.",
            "3. To touch y=0, the center must be at y=a/2 or y=-a/2.",
            "4. The resulting equations are:", indented_math(result)
        ])
        return "\n".join(lines)

    # 2. Line Derivation Case
    if "Line(" in expr_str and ".equation" in expr_str:
        lines.extend([
            "1. Identify the points or slope provided for the line.",
            "2. Use the point-slope form: y - y₁ = m(x - x₁).",
            "3. Simplify into the general form ax + by + c = 0.",
            "4. The line equation is:", indented_math(result)
        ])
        return "\n".join(lines)

    # 3. Distance Case
    if "distance(" in expr_str:
        lines.extend([
            "1. Identify the geometric entities (Point, Line, or Plane).",
            "2. Apply the perpendicular distance formula.",
            f"3. The calculated distance is:", indented_math(result)
        ])
        return "\n".join(lines)

    # 4. Conics / Circle Standard evaluation
    if any(conic in expr_str for conic in ["Circle(", "Ellipse(", "Parabola("]):
        lines.extend([
            "1. Define the conic section using its focus, directrix, or eccentricity.",
            "2. Convert the geometric definition into an algebraic equation.",
            "3. The result is:", indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "evaluate":
        lines.extend(["1. Analyze the geometric properties.", "2. Final result:", indented_math(result)])
        return "\n".join(lines)

    return None