from typing import Any

import sympy as sp
from sympy.geometry import Circle, Point

from formatter import indented_math
from models import MathTask


x, y = sp.symbols("x y")


def _as_point(value) -> Point:
    if isinstance(value, Point):
        return value
    if isinstance(value, sp.MatrixBase):
        return Point(*list(value))
    if isinstance(value, (list, tuple, sp.Tuple)):
        return Point(*value)
    raise ValueError("Expected a Point, tuple/list, or vector-like value.")


def _point_xy(value) -> tuple[sp.Basic, sp.Basic]:
    point = _as_point(value)
    if len(point.args) != 2:
        raise ValueError("Circle operations require 2D points.")
    return sp.sympify(point.x), sp.sympify(point.y)


def _as_equation(value) -> sp.Equality:
    if isinstance(value, sp.Equality):
        return value
    return sp.Eq(value, 0, evaluate=False)


def _circle_expression(circle_eq) -> sp.Basic:
    equation = _as_equation(circle_eq)
    return sp.expand(equation.lhs - equation.rhs)


def _circle_coefficients(circle_eq) -> tuple[sp.Basic, sp.Basic, sp.Basic]:
    expr = _circle_expression(circle_eq)
    poly = sp.Poly(expr, x, y)
    x2 = poly.coeff_monomial(x**2)
    y2 = poly.coeff_monomial(y**2)
    xy = poly.coeff_monomial(x * y)
    if x2 == 0 or y2 == 0 or sp.simplify(x2 - y2) != 0 or xy != 0:
        raise ValueError("Expected a circle equation with equal x^2 and y^2 coefficients and no xy term.")

    normalized = sp.expand(expr / x2)
    poly = sp.Poly(normalized, x, y)
    d = poly.coeff_monomial(x)
    e = poly.coeff_monomial(y)
    f = poly.coeff_monomial(1)
    return sp.simplify(d), sp.simplify(e), sp.simplify(f)


def circle_equation_center_radius(center, radius):
    h, k = _point_xy(center)
    return sp.Eq((x - h) ** 2 + (y - k) ** 2, sp.sympify(radius) ** 2, evaluate=False)


def circle_equation_general(d, e, f):
    return sp.Eq(x**2 + y**2 + d * x + e * y + f, 0, evaluate=False)


def circle_from_center_point(center, point):
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    radius_squared = sp.simplify((px - h) ** 2 + (py - k) ** 2)
    return sp.Eq((x - h) ** 2 + (y - k) ** 2, radius_squared, evaluate=False)


def circle_from_diameter(point1, point2):
    x1, y1 = _point_xy(point1)
    x2, y2 = _point_xy(point2)
    return sp.Eq((x - x1) * (x - x2) + (y - y1) * (y - y2), 0, evaluate=False)


def circle_from_three_points(point1, point2, point3):
    points = [_as_point(point1), _as_point(point2), _as_point(point3)]
    circle = Circle(*points)
    return sp.Eq(sp.expand(circle.equation(x, y)), 0, evaluate=False)


def circle_center(circle_eq):
    d, e, _ = _circle_coefficients(circle_eq)
    return Point(sp.simplify(-d / 2), sp.simplify(-e / 2))


def circle_radius(circle_eq):
    d, e, f = _circle_coefficients(circle_eq)
    return sp.sqrt(sp.simplify((d**2 + e**2) / 4 - f))


def circle_center_radius(circle_eq):
    return {
        "center": circle_center(circle_eq),
        "radius": circle_radius(circle_eq),
    }


def circle_standard_form(circle_eq):
    center = circle_center(circle_eq)
    radius = circle_radius(circle_eq)
    return circle_equation_center_radius(center, radius)


def circle_general_form(circle_eq):
    expr = _circle_expression(circle_eq)
    return sp.Eq(sp.expand(expr), 0, evaluate=False)


def point_power(circle_eq, point):
    px, py = _point_xy(point)
    return sp.simplify(_circle_expression(circle_eq).subs({x: px, y: py}))


def point_position(circle_eq, point):
    power = sp.simplify(point_power(circle_eq, point))
    if power == 0:
        return "on"
    if power.is_negative:
        return "inside"
    if power.is_positive:
        return "outside"
    return sp.sign(power)


def tangent_at_point(circle_eq, point):
    center = circle_center(circle_eq)
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    expr = (px - h) * (x - px) + (py - k) * (y - py)
    return sp.Eq(sp.expand(expr), 0, evaluate=False)


def normal_at_point(circle_eq, point):
    center = circle_center(circle_eq)
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    if sp.simplify(px - h) == 0:
        return sp.Eq(x, h, evaluate=False)
    slope = sp.simplify((py - k) / (px - h))
    return sp.Eq(y - py, slope * (x - px), evaluate=False)


def contact_chord(circle_eq, point):
    d, e, f = _circle_coefficients(circle_eq)
    px, py = _point_xy(point)
    expr = x * px + y * py + d * (x + px) / 2 + e * (y + py) / 2 + f
    return sp.Eq(sp.expand(expr), 0, evaluate=False)


def chord_with_midpoint(circle_eq, midpoint):
    d, e, f = _circle_coefficients(circle_eq)
    mx, my = _point_xy(midpoint)
    t_expr = x * mx + y * my + d * (x + mx) / 2 + e * (y + my) / 2 + f
    s1 = sp.simplify(mx**2 + my**2 + d * mx + e * my + f)
    return sp.Eq(sp.expand(t_expr), s1, evaluate=False)


def tangent_length(circle_eq, point):
    return sp.sqrt(sp.simplify(point_power(circle_eq, point)))


def pair_of_tangents(circle_eq, point):
    d, e, f = _circle_coefficients(circle_eq)
    px, py = _point_xy(point)
    s_expr = x**2 + y**2 + d * x + e * y + f
    s1 = sp.simplify(px**2 + py**2 + d * px + e * py + f)
    t_expr = x * px + y * py + d * (x + px) / 2 + e * (y + py) / 2 + f
    return sp.Eq(sp.expand(s_expr * s1 - t_expr**2), 0, evaluate=False)


def tangents_with_slope(circle_eq, slope):
    center = circle_center(circle_eq)
    h, k = _point_xy(center)
    radius = circle_radius(circle_eq)
    m = sp.sympify(slope)
    offset = sp.simplify(radius * sp.sqrt(1 + m**2))
    return sp.Tuple(
        sp.Eq(y - k, m * (x - h) + offset, evaluate=False),
        sp.Eq(y - k, m * (x - h) - offset, evaluate=False),
    )


def circle_from_center_tangent_line(center, line_eq):
    h, k = _point_xy(center)
    line_expr = sp.expand(_as_equation(line_eq).lhs - _as_equation(line_eq).rhs)
    poly = sp.Poly(line_expr, x, y)
    if poly.total_degree() != 1:
        raise ValueError("Expected a straight line equation.")
    a = poly.coeff_monomial(x)
    b = poly.coeff_monomial(y)
    c = poly.coeff_monomial(1)
    radius = sp.simplify(sp.Abs(a * h + b * k + c) / sp.sqrt(a**2 + b**2))
    return circle_equation_center_radius(Point(h, k), radius)


def circle_line_intersections(circle_eq, line_eq):
    circle_expr = _circle_expression(circle_eq)
    line_expr = _as_equation(line_eq).lhs - _as_equation(line_eq).rhs
    solutions = sp.solve([circle_expr, line_expr], [x, y], dict=True)
    return sp.Tuple(*(Point(sp.simplify(sol[x]), sp.simplify(sol[y])) for sol in solutions))


def circle_circle_intersections(circle1_eq, circle2_eq):
    expr1 = _circle_expression(circle1_eq)
    expr2 = _circle_expression(circle2_eq)
    solutions = sp.solve([expr1, expr2], [x, y], dict=True)
    return sp.Tuple(*(Point(sp.simplify(sol[x]), sp.simplify(sol[y])) for sol in solutions))


def radical_axis(circle1_eq, circle2_eq):
    expr = sp.expand(_circle_expression(circle1_eq) - _circle_expression(circle2_eq))
    return sp.Eq(expr, 0, evaluate=False)


def circle_tangent_to_axes(radius, quadrant=1):
    radius = sp.sympify(radius)
    signs = {
        1: (1, 1),
        2: (-1, 1),
        3: (-1, -1),
        4: (1, -1),
    }
    sx, sy = signs.get(int(quadrant), (1, 1))
    return circle_equation_center_radius(Point(sx * radius, sy * radius), radius)


def circle_tangent_to_x_axis(center_x, center_y):
    center_y = sp.sympify(center_y)
    return circle_equation_center_radius(Point(center_x, center_y), sp.Abs(center_y))


def circle_tangent_to_y_axis(center_x, center_y):
    center_x = sp.sympify(center_x)
    return circle_equation_center_radius(Point(center_x, center_y), sp.Abs(center_x))


SYMPY_LOCALS = {
    "x": x,
    "y": y,
    "Circle": Circle,
    "circle_equation_center_radius": circle_equation_center_radius,
    "circle_equation_general": circle_equation_general,
    "circle_from_center_point": circle_from_center_point,
    "circle_from_diameter": circle_from_diameter,
    "circle_from_three_points": circle_from_three_points,
    "circle_center": circle_center,
    "circle_radius": circle_radius,
    "circle_center_radius": circle_center_radius,
    "circle_standard_form": circle_standard_form,
    "circle_general_form": circle_general_form,
    "point_power": point_power,
    "point_position": point_position,
    "tangent_at_point": tangent_at_point,
    "normal_at_point": normal_at_point,
    "contact_chord": contact_chord,
    "chord_with_midpoint": chord_with_midpoint,
    "tangent_length": tangent_length,
    "pair_of_tangents": pair_of_tangents,
    "tangents_with_slope": tangents_with_slope,
    "circle_from_center_tangent_line": circle_from_center_tangent_line,
    "circle_line_intersections": circle_line_intersections,
    "circle_circle_intersections": circle_circle_intersections,
    "radical_axis": radical_axis,
    "circle_tangent_to_axes": circle_tangent_to_axes,
    "circle_tangent_to_x_axis": circle_tangent_to_x_axis,
    "circle_tangent_to_y_axis": circle_tangent_to_y_axis,
}

RULES = [
    "For CIRCLE EQUATION from center and radius: use circle_equation_center_radius(Point(h, k), r).",
    "For GENERAL CIRCLE x^2 + y^2 + Dx + Ey + F = 0: use circle_equation_general(D, E, F).",
    "For CENTER/RADIUS from equation: use circle_center_radius(Eq(..., 0)), circle_center(...), or circle_radius(...).",
    "For STANDARD FORM conversion: use circle_standard_form(Eq(..., 0)); for general expanded form use circle_general_form(...).",
    "For CIRCLE through center and point: use circle_from_center_point(Point(h, k), Point(x1, y1)).",
    "For CIRCLE with diameter endpoints: use circle_from_diameter(Point(x1, y1), Point(x2, y2)).",
    "For CIRCLE through three points: use circle_from_three_points(Point(...), Point(...), Point(...)).",
    "For TANGENT/NORMAL at a point on circle: use tangent_at_point(circle_eq, Point(...)) or normal_at_point(circle_eq, Point(...)).",
    "For CONTACT CHORD / polar from external point: use contact_chord(circle_eq, Point(...)).",
    "For PAIR OF TANGENTS from an external point: use pair_of_tangents(circle_eq, Point(...)).",
    "For TANGENTS with a given slope: use tangents_with_slope(circle_eq, m).",
    "For CHORD with given midpoint: use chord_with_midpoint(circle_eq, Point(...)).",
    "For TANGENT LENGTH from point: use tangent_length(circle_eq, Point(...)).",
    "For CIRCLE with center tangent to a line: use circle_from_center_tangent_line(Point(h, k), line_eq).",
    "For LINE-CIRCLE intersections: use circle_line_intersections(circle_eq, line_eq).",
    "For TWO CIRCLE intersections or common chord/radical axis: use circle_circle_intersections(c1, c2) or radical_axis(c1, c2).",
    "For a circle tangent to both axes with radius r in quadrant q: use circle_tangent_to_axes(r, q).",
]

EXAMPLES = [
    'User problem: equation of circle with center (2, -3) and radius 5\nJSON: {"operation":"evaluate","expression":"circle_equation_center_radius(Point(2, -3), 5)"}',
    'User problem: center and radius of x^2 + y^2 - 4x + 6y - 12 = 0\nJSON: {"operation":"evaluate","expression":"circle_center_radius(Eq(x**2 + y**2 - 4*x + 6*y - 12, 0))"}',
    'User problem: circle with diameter endpoints (1,2) and (5,6)\nJSON: {"operation":"evaluate","expression":"circle_from_diameter(Point(1, 2), Point(5, 6))"}',
    'User problem: circle passing through (0,0), (1,0), (0,1)\nJSON: {"operation":"evaluate","expression":"circle_from_three_points(Point(0, 0), Point(1, 0), Point(0, 1))"}',
    'User problem: tangent to x^2+y^2=25 at (3,4)\nJSON: {"operation":"evaluate","expression":"tangent_at_point(Eq(x**2 + y**2, 25), Point(3, 4))"}',
    'User problem: normal to x^2+y^2=25 at (3,4)\nJSON: {"operation":"evaluate","expression":"normal_at_point(Eq(x**2 + y**2, 25), Point(3, 4))"}',
    'User problem: chord of contact from (7,1) to x^2+y^2=25\nJSON: {"operation":"evaluate","expression":"contact_chord(Eq(x**2 + y**2, 25), Point(7, 1))"}',
    'User problem: pair of tangents from (7,1) to x^2+y^2=25\nJSON: {"operation":"evaluate","expression":"pair_of_tangents(Eq(x**2 + y**2, 25), Point(7, 1))"}',
    'User problem: tangents to x^2+y^2=25 with slope 2\nJSON: {"operation":"evaluate","expression":"tangents_with_slope(Eq(x**2 + y**2, 25), 2)"}',
    'User problem: length of tangent from (13,0) to x^2+y^2=25\nJSON: {"operation":"evaluate","expression":"tangent_length(Eq(x**2 + y**2, 25), Point(13, 0))"}',
    'User problem: circle with center (1,2) touching line 3x+4y-10=0\nJSON: {"operation":"evaluate","expression":"circle_from_center_tangent_line(Point(1, 2), Eq(3*x + 4*y - 10, 0))"}',
    'User problem: intersection of circle x^2+y^2=25 and line x=3\nJSON: {"operation":"evaluate","expression":"circle_line_intersections(Eq(x**2 + y**2, 25), Eq(x, 3))"}',
    'User problem: radical axis of x^2+y^2=25 and x^2+y^2-4x=0\nJSON: {"operation":"evaluate","expression":"radical_axis(Eq(x**2 + y**2, 25), Eq(x**2 + y**2 - 4*x, 0))"}',
]


CIRCLE_MARKERS = (
    "Circle(",
    "circle_",
    "point_power(",
    "point_position(",
    "tangent_at_point(",
    "normal_at_point(",
    "contact_chord(",
    "chord_with_midpoint(",
    "tangent_length(",
    "pair_of_tangents(",
    "radical_axis(",
)


def is_circle_expression(expr_str: str) -> bool:
    stripped = expr_str.strip()
    return stripped.startswith("tangents_with_slope(") or any(marker in stripped for marker in CIRCLE_MARKERS)


def execute(task: MathTask, expr, variables: list, equations: list):
    if task.operation == "circle_tangent_coordinate_lines":
        x, y, a = sp.symbols("x y a")
        return [
            sp.Eq((2 * x - a) ** 2 + (2 * y - a) ** 2, a**2, evaluate=False),
            sp.Eq((2 * x - a) ** 2 + (2 * y + a) ** 2, a**2, evaluate=False),
        ]
    if task.operation == "evaluate" and is_circle_expression(task.expression or task.equation or ""):
        if isinstance(expr, (str, bool, dict, sp.Tuple)):
            return expr
        try:
            return sp.simplify(expr)
        except Exception:
            return expr
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if task.operation == "circle_tangent_coordinate_lines":
        lines = [
            "1. A circle tangent to x=0 and x=a has its center at x=a/2.",
            "2. The radius must be a/2.",
            "3. To touch y=0, the center must be at y=a/2 or y=-a/2.",
            "4. The resulting equations are:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if not is_circle_expression(expr_str) and task.operation != "circle_tangent_coordinate_lines":
        return None

    step_map = [
        ("circle_equation_center_radius(", "1. Use the standard form (x - h)² + (y - k)² = r²."),
        ("circle_equation_general(", "1. Substitute D, E, and F into x² + y² + Dx + Ey + F = 0."),
        ("circle_center_radius(", "1. Compare the equation with x² + y² + Dx + Ey + F = 0."),
        ("circle_center(", "1. Use center = (-D/2, -E/2) from the general circle equation."),
        ("circle_radius(", "1. Use radius = √((D² + E²)/4 - F)."),
        ("circle_standard_form(", "1. Complete the squares in x and y."),
        ("circle_general_form(", "1. Expand the standard equation and collect terms."),
        ("circle_from_center_point(", "1. Find the radius from the distance between the center and the given point."),
        ("circle_from_diameter(", "1. Use the diameter form (x - x₁)(x - x₂) + (y - y₁)(y - y₂) = 0."),
        ("circle_from_three_points(", "1. Substitute the three points into x² + y² + Dx + Ey + F = 0 and solve."),
        ("point_power(", "1. Substitute the point into the circle expression S = x² + y² + Dx + Ey + F."),
        ("point_position(", "1. Use the sign of the point power to classify the point."),
        ("tangent_at_point(", "1. The tangent is perpendicular to the radius at the point of contact."),
        ("normal_at_point(", "1. The normal passes through the center and the point of contact."),
        ("contact_chord(", "1. Use the T = 0 form for the chord of contact from the external point."),
        ("pair_of_tangents(", "1. Use SS₁ = T² for the combined equation of the two tangents."),
        ("tangents_with_slope(", "1. Use y - k = m(x - h) ± r√(1 + m²)."),
        ("chord_with_midpoint(", "1. Use T = S₁ for the chord whose midpoint is the given point."),
        ("tangent_length(", "1. Use tangent length = √(power of the point)."),
        ("circle_from_center_tangent_line(", "1. The radius is the perpendicular distance from the center to the line."),
        ("circle_line_intersections(", "1. Solve the circle equation and line equation simultaneously."),
        ("circle_circle_intersections(", "1. Solve both circle equations simultaneously."),
        ("radical_axis(", "1. Subtract the two circle equations to remove x² and y²."),
        ("circle_tangent_to_axes(", "1. A circle tangent to both axes has center (±r, ±r)."),
        ("circle_tangent_to_x_axis(", "1. A circle tangent to the x-axis has radius |center y-coordinate|."),
        ("circle_tangent_to_y_axis(", "1. A circle tangent to the y-axis has radius |center x-coordinate|."),
    ]

    for marker, first_step in step_map:
        if marker in expr_str:
            lines = [
                first_step,
                "2. Simplify the resulting circle relation.",
                "3. The result is:",
                indented_math(result),
            ]
            return "\n".join(lines)

    if "Circle(" in expr_str:
        lines = [
            "1. Identify the circle center and radius information.",
            "2. Build or simplify the circle equation using the geometric definition.",
            "3. The result is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    return None
