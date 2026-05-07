from typing import Any

import sympy as sp
from sympy.geometry import Ellipse, Parabola, Point

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
    raise ValueError("Expected a 2D point.")


def _point_xy(value) -> tuple[sp.Basic, sp.Basic]:
    point = _as_point(value)
    if len(point.args) != 2:
        raise ValueError("Conic operations require 2D points.")
    return sp.sympify(point.x), sp.sympify(point.y)


def _as_equation(value) -> sp.Equality:
    if isinstance(value, sp.Equality):
        return value
    return sp.Eq(value, 0, evaluate=False)


def _expression(eq_or_expr) -> sp.Basic:
    equation = _as_equation(eq_or_expr)
    return sp.expand(equation.lhs - equation.rhs)


def _line_coefficients(line_eq) -> tuple[sp.Basic, sp.Basic, sp.Basic]:
    expr = _expression(line_eq)
    poly = sp.Poly(expr, x, y)
    if poly.total_degree() > 1:
        raise ValueError("Expected a straight line equation.")
    return (
        sp.simplify(poly.coeff_monomial(x)),
        sp.simplify(poly.coeff_monomial(y)),
        sp.simplify(poly.coeff_monomial(1)),
    )


def _second_degree_coefficients(eq_or_expr):
    expr = _expression(eq_or_expr)
    poly = sp.Poly(expr, x, y)
    return {
        "A": sp.simplify(poly.coeff_monomial(x**2)),
        "B": sp.simplify(poly.coeff_monomial(x * y)),
        "C": sp.simplify(poly.coeff_monomial(y**2)),
        "D": sp.simplify(poly.coeff_monomial(x)),
        "E": sp.simplify(poly.coeff_monomial(y)),
        "F": sp.simplify(poly.coeff_monomial(1)),
    }


# --- Pair Of Straight Lines ---


def pair_lines_product(line1_eq, line2_eq):
    return sp.Eq(sp.expand(_expression(line1_eq) * _expression(line2_eq)), 0, evaluate=False)


def pair_lines_from_homogeneous(a, h, b):
    return sp.Eq(a * x**2 + 2 * h * x * y + b * y**2, 0, evaluate=False)


def pair_lines_from_coefficients(a, h, b, g=0, f=0, c=0):
    return sp.Eq(a * x**2 + 2 * h * x * y + b * y**2 + 2 * g * x + 2 * f * y + c, 0, evaluate=False)


def pair_lines_condition(a, h, b, g=0, f=0, c=0):
    return sp.simplify(a * b * c + 2 * f * g * h - a * f**2 - b * g**2 - c * h**2)


def is_pair_of_lines(eq_or_expr):
    coeffs = _second_degree_coefficients(eq_or_expr)
    a = coeffs["A"]
    h = coeffs["B"] / 2
    b = coeffs["C"]
    g = coeffs["D"] / 2
    f = coeffs["E"] / 2
    c = coeffs["F"]
    return sp.simplify(pair_lines_condition(a, h, b, g, f, c)) == 0


def pair_lines_factor(eq_or_expr):
    expr = _expression(eq_or_expr)
    return sp.factor(expr)


def pair_lines_separate(eq_or_expr):
    factored = sp.factor(_expression(eq_or_expr))
    factors = factored.args if factored.is_Mul else (factored,)
    line_factors = [factor for factor in factors if sp.Poly(factor, x, y).total_degree() == 1]
    if len(line_factors) >= 2:
        return sp.Tuple(*(sp.Eq(factor, 0, evaluate=False) for factor in line_factors[:2]))
    return sp.solve(sp.Eq(factored, 0), y)


def pair_lines_slopes_homogeneous(a, h, b):
    m = sp.Symbol("m")
    return sp.Tuple(*sp.solve(sp.Eq(b * m**2 + 2 * h * m + a, 0), m))


def pair_lines_angle_homogeneous(a, h, b):
    return sp.atan(sp.simplify(2 * sp.sqrt(h**2 - a * b) / (a + b)))


def pair_lines_intersection(line1_eq, line2_eq):
    a1, b1, c1 = _line_coefficients(line1_eq)
    a2, b2, c2 = _line_coefficients(line2_eq)
    solution = sp.solve([a1 * x + b1 * y + c1, a2 * x + b2 * y + c2], [x, y], dict=True)
    if not solution:
        return None
    return Point(sp.simplify(solution[0][x]), sp.simplify(solution[0][y]))


# --- Parabola ---


def parabola_standard(a, orientation="right"):
    a = sp.sympify(a)
    if orientation == "right":
        return sp.Eq(y**2, 4 * a * x, evaluate=False)
    if orientation == "left":
        return sp.Eq(y**2, -4 * a * x, evaluate=False)
    if orientation == "up":
        return sp.Eq(x**2, 4 * a * y, evaluate=False)
    if orientation == "down":
        return sp.Eq(x**2, -4 * a * y, evaluate=False)
    raise ValueError("orientation must be right, left, up, or down.")


def parabola_properties(a, orientation="right"):
    a = sp.sympify(a)
    if orientation == "right":
        return {"vertex": Point(0, 0), "focus": Point(a, 0), "directrix": sp.Eq(x, -a), "axis": sp.Eq(y, 0), "latus_rectum": 4 * a}
    if orientation == "left":
        return {"vertex": Point(0, 0), "focus": Point(-a, 0), "directrix": sp.Eq(x, a), "axis": sp.Eq(y, 0), "latus_rectum": 4 * a}
    if orientation == "up":
        return {"vertex": Point(0, 0), "focus": Point(0, a), "directrix": sp.Eq(y, -a), "axis": sp.Eq(x, 0), "latus_rectum": 4 * a}
    if orientation == "down":
        return {"vertex": Point(0, 0), "focus": Point(0, -a), "directrix": sp.Eq(y, a), "axis": sp.Eq(x, 0), "latus_rectum": 4 * a}
    raise ValueError("orientation must be right, left, up, or down.")


def parabola_point(a, t, orientation="right"):
    a = sp.sympify(a)
    t = sp.sympify(t)
    if orientation == "right":
        return Point(a * t**2, 2 * a * t)
    if orientation == "left":
        return Point(-a * t**2, 2 * a * t)
    if orientation == "up":
        return Point(2 * a * t, a * t**2)
    if orientation == "down":
        return Point(2 * a * t, -a * t**2)
    raise ValueError("orientation must be right, left, up, or down.")


def parabola_tangent(a, point_or_t, orientation="right"):
    a = sp.sympify(a)
    if isinstance(point_or_t, Point):
        px, py = _point_xy(point_or_t)
        if orientation in {"right", "left"}:
            sign = 1 if orientation == "right" else -1
            return sp.Eq(y * py, 2 * sign * a * (x + px), evaluate=False)
        sign = 1 if orientation == "up" else -1
        return sp.Eq(x * px, 2 * sign * a * (y + py), evaluate=False)

    t = sp.sympify(point_or_t)
    if orientation == "right":
        return sp.Eq(t * y, x + a * t**2, evaluate=False)
    if orientation == "left":
        return sp.Eq(t * y, -x + a * t**2, evaluate=False)
    if orientation == "up":
        return sp.Eq(t * x, y + a * t**2, evaluate=False)
    if orientation == "down":
        return sp.Eq(t * x, -y + a * t**2, evaluate=False)
    raise ValueError("orientation must be right, left, up, or down.")


def parabola_normal(a, t, orientation="right"):
    a = sp.sympify(a)
    t = sp.sympify(t)
    if orientation == "right":
        return sp.Eq(y, -t * x + 2 * a * t + a * t**3, evaluate=False)
    if orientation == "left":
        return sp.Eq(y, t * x + 2 * a * t + a * t**3, evaluate=False)
    if orientation == "up":
        return sp.Eq(x, -t * y + 2 * a * t + a * t**3, evaluate=False)
    if orientation == "down":
        return sp.Eq(x, t * y + 2 * a * t + a * t**3, evaluate=False)
    raise ValueError("orientation must be right, left, up, or down.")


def parabola_from_focus_directrix(focus, directrix_eq):
    fx, fy = _point_xy(focus)
    a, b, c = _line_coefficients(directrix_eq)
    distance_line_squared = (a * x + b * y + c) ** 2 / (a**2 + b**2)
    distance_focus_squared = (x - fx) ** 2 + (y - fy) ** 2
    return sp.Eq(sp.expand(distance_focus_squared - distance_line_squared), 0, evaluate=False)


def conic_from_focus_directrix(focus, directrix_eq, eccentricity):
    fx, fy = _point_xy(focus)
    a, b, c = _line_coefficients(directrix_eq)
    e = sp.sympify(eccentricity)
    distance_line_squared = (a * x + b * y + c) ** 2 / (a**2 + b**2)
    distance_focus_squared = (x - fx) ** 2 + (y - fy) ** 2
    return sp.Eq(sp.expand(distance_focus_squared - e**2 * distance_line_squared), 0, evaluate=False)


# --- Ellipse ---


def ellipse_standard(a, b, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    if orientation == "horizontal":
        return sp.Eq((x - h) ** 2 / a**2 + (y - k) ** 2 / b**2, 1, evaluate=False)
    if orientation == "vertical":
        return sp.Eq((x - h) ** 2 / b**2 + (y - k) ** 2 / a**2, 1, evaluate=False)
    raise ValueError("orientation must be horizontal or vertical.")


def ellipse_properties(a, b, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    c = sp.sqrt(a**2 - b**2)
    e = sp.simplify(c / a)
    if orientation == "horizontal":
        return {
            "center": Point(h, k),
            "eccentricity": e,
            "foci": sp.Tuple(Point(h - c, k), Point(h + c, k)),
            "vertices": sp.Tuple(Point(h - a, k), Point(h + a, k)),
            "minor_vertices": sp.Tuple(Point(h, k - b), Point(h, k + b)),
            "directrices": sp.Tuple(sp.Eq(x, h - a / e), sp.Eq(x, h + a / e)),
            "latus_rectum": sp.simplify(2 * b**2 / a),
        }
    if orientation == "vertical":
        return {
            "center": Point(h, k),
            "eccentricity": e,
            "foci": sp.Tuple(Point(h, k - c), Point(h, k + c)),
            "vertices": sp.Tuple(Point(h, k - a), Point(h, k + a)),
            "minor_vertices": sp.Tuple(Point(h - b, k), Point(h + b, k)),
            "directrices": sp.Tuple(sp.Eq(y, k - a / e), sp.Eq(y, k + a / e)),
            "latus_rectum": sp.simplify(2 * b**2 / a),
        }
    raise ValueError("orientation must be horizontal or vertical.")


def ellipse_tangent(a, b, point, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    a = sp.sympify(a)
    b = sp.sympify(b)
    if orientation == "horizontal":
        return sp.Eq((x - h) * (px - h) / a**2 + (y - k) * (py - k) / b**2, 1, evaluate=False)
    if orientation == "vertical":
        return sp.Eq((x - h) * (px - h) / b**2 + (y - k) * (py - k) / a**2, 1, evaluate=False)
    raise ValueError("orientation must be horizontal or vertical.")


def ellipse_tangents_with_slope(a, b, slope, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    m = sp.sympify(slope)
    if orientation == "horizontal":
        offset = sp.sqrt(a**2 * m**2 + b**2)
    elif orientation == "vertical":
        offset = sp.sqrt(b**2 * m**2 + a**2)
    else:
        raise ValueError("orientation must be horizontal or vertical.")
    return sp.Tuple(
        sp.Eq(y - k, m * (x - h) + offset, evaluate=False),
        sp.Eq(y - k, m * (x - h) - offset, evaluate=False),
    )


def ellipse_normal(a, b, point, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    a = sp.sympify(a)
    b = sp.sympify(b)
    X = x - h
    Y = y - k
    X1 = px - h
    Y1 = py - k
    if X1 == 0 or Y1 == 0:
        raise ValueError("Use axis line normal for points with zero shifted coordinate.")
    if orientation == "horizontal":
        return sp.Eq(a**2 * X / X1 - b**2 * Y / Y1, a**2 - b**2, evaluate=False)
    if orientation == "vertical":
        return sp.Eq(b**2 * X / X1 - a**2 * Y / Y1, b**2 - a**2, evaluate=False)
    raise ValueError("orientation must be horizontal or vertical.")


# --- Hyperbola ---


def hyperbola_standard(a, b, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    if orientation == "horizontal":
        return sp.Eq((x - h) ** 2 / a**2 - (y - k) ** 2 / b**2, 1, evaluate=False)
    if orientation == "vertical":
        return sp.Eq((y - k) ** 2 / a**2 - (x - h) ** 2 / b**2, 1, evaluate=False)
    raise ValueError("orientation must be horizontal or vertical.")


def hyperbola_properties(a, b, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    c = sp.sqrt(a**2 + b**2)
    e = sp.simplify(c / a)
    if orientation == "horizontal":
        return {
            "center": Point(h, k),
            "eccentricity": e,
            "foci": sp.Tuple(Point(h - c, k), Point(h + c, k)),
            "vertices": sp.Tuple(Point(h - a, k), Point(h + a, k)),
            "directrices": sp.Tuple(sp.Eq(x, h - a / e), sp.Eq(x, h + a / e)),
            "asymptotes": sp.Tuple(sp.Eq(y - k, b * (x - h) / a), sp.Eq(y - k, -b * (x - h) / a)),
            "latus_rectum": sp.simplify(2 * b**2 / a),
        }
    if orientation == "vertical":
        return {
            "center": Point(h, k),
            "eccentricity": e,
            "foci": sp.Tuple(Point(h, k - c), Point(h, k + c)),
            "vertices": sp.Tuple(Point(h, k - a), Point(h, k + a)),
            "directrices": sp.Tuple(sp.Eq(y, k - a / e), sp.Eq(y, k + a / e)),
            "asymptotes": sp.Tuple(sp.Eq(y - k, a * (x - h) / b), sp.Eq(y - k, -a * (x - h) / b)),
            "latus_rectum": sp.simplify(2 * b**2 / a),
        }
    raise ValueError("orientation must be horizontal or vertical.")


def hyperbola_tangent(a, b, point, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    px, py = _point_xy(point)
    a = sp.sympify(a)
    b = sp.sympify(b)
    if orientation == "horizontal":
        return sp.Eq((x - h) * (px - h) / a**2 - (y - k) * (py - k) / b**2, 1, evaluate=False)
    if orientation == "vertical":
        return sp.Eq((y - k) * (py - k) / a**2 - (x - h) * (px - h) / b**2, 1, evaluate=False)
    raise ValueError("orientation must be horizontal or vertical.")


def hyperbola_tangents_with_slope(a, b, slope, center=Point(0, 0), orientation="horizontal"):
    h, k = _point_xy(center)
    a = sp.sympify(a)
    b = sp.sympify(b)
    m = sp.sympify(slope)
    if orientation == "horizontal":
        offset = sp.sqrt(a**2 * m**2 - b**2)
    elif orientation == "vertical":
        offset = sp.sqrt(b**2 * m**2 - a**2)
    else:
        raise ValueError("orientation must be horizontal or vertical.")
    return sp.Tuple(
        sp.Eq(y - k, m * (x - h) + offset, evaluate=False),
        sp.Eq(y - k, m * (x - h) - offset, evaluate=False),
    )


def rectangular_hyperbola(c):
    c = sp.sympify(c)
    return sp.Eq(x * y, c**2, evaluate=False)


def rectangular_hyperbola_tangent(c, point):
    c = sp.sympify(c)
    px, py = _point_xy(point)
    return sp.Eq(x * py + y * px, 2 * c**2, evaluate=False)


def conic_classify(eq_or_expr):
    coeffs = _second_degree_coefficients(eq_or_expr)
    discriminant = sp.simplify(coeffs["B"] ** 2 - 4 * coeffs["A"] * coeffs["C"])
    if discriminant == 0:
        return "parabola"
    if discriminant.is_negative:
        return "ellipse"
    if discriminant.is_positive:
        return "hyperbola"
    return {"discriminant": discriminant}


SYMPY_LOCALS = {
    "x": x,
    "y": y,
    "Ellipse": Ellipse,
    "Parabola": Parabola,
    "pair_lines_product": pair_lines_product,
    "pair_lines_from_homogeneous": pair_lines_from_homogeneous,
    "pair_lines_from_coefficients": pair_lines_from_coefficients,
    "pair_lines_condition": pair_lines_condition,
    "is_pair_of_lines": is_pair_of_lines,
    "pair_lines_factor": pair_lines_factor,
    "pair_lines_separate": pair_lines_separate,
    "pair_lines_slopes_homogeneous": pair_lines_slopes_homogeneous,
    "pair_lines_angle_homogeneous": pair_lines_angle_homogeneous,
    "pair_lines_intersection": pair_lines_intersection,
    "parabola_standard": parabola_standard,
    "parabola_properties": parabola_properties,
    "parabola_point": parabola_point,
    "parabola_tangent": parabola_tangent,
    "parabola_normal": parabola_normal,
    "parabola_from_focus_directrix": parabola_from_focus_directrix,
    "conic_from_focus_directrix": conic_from_focus_directrix,
    "ellipse_standard": ellipse_standard,
    "ellipse_properties": ellipse_properties,
    "ellipse_tangent": ellipse_tangent,
    "ellipse_tangents_with_slope": ellipse_tangents_with_slope,
    "ellipse_normal": ellipse_normal,
    "hyperbola_standard": hyperbola_standard,
    "hyperbola_properties": hyperbola_properties,
    "hyperbola_tangent": hyperbola_tangent,
    "hyperbola_tangents_with_slope": hyperbola_tangents_with_slope,
    "rectangular_hyperbola": rectangular_hyperbola,
    "rectangular_hyperbola_tangent": rectangular_hyperbola_tangent,
    "conic_classify": conic_classify,
}

RULES = [
    "For PAIR OF STRAIGHT LINES: use pair_lines_product(line1, line2), pair_lines_factor(eq), pair_lines_separate(eq), pair_lines_condition(a,h,b,g,f,c), or pair_lines_angle_homogeneous(a,h,b).",
    "For homogeneous pair ax^2 + 2hxy + by^2 = 0: use pair_lines_from_homogeneous(a,h,b), pair_lines_slopes_homogeneous(a,h,b), or pair_lines_angle_homogeneous(a,h,b).",
    "For PARABOLA standard forms: use parabola_standard(a,'right') for y^2=4ax, 'left' for y^2=-4ax, 'up' for x^2=4ay, 'down' for x^2=-4ay.",
    "For PARABOLA properties: use parabola_properties(a, orientation). For parametric point use parabola_point(a,t,orientation).",
    "For PARABOLA tangent/normal: use parabola_tangent(a, point_or_t, orientation) and parabola_normal(a,t,orientation).",
    "For PARABOLA from focus and directrix: use parabola_from_focus_directrix(Point(...), Eq(line,0)).",
    "For GENERAL focus-directrix conic with eccentricity e: use conic_from_focus_directrix(Point(...), Eq(line,0), e). Use e=1 parabola, e<1 ellipse, e>1 hyperbola.",
    "For ELLIPSE standard form: use ellipse_standard(a,b,Point(h,k),'horizontal'/'vertical').",
    "For ELLIPSE properties/tangent/normal/slope tangents: use ellipse_properties, ellipse_tangent, ellipse_normal, ellipse_tangents_with_slope.",
    "For HYPERBOLA standard form: use hyperbola_standard(a,b,Point(h,k),'horizontal'/'vertical').",
    "For HYPERBOLA properties/tangent/slope tangents: use hyperbola_properties, hyperbola_tangent, hyperbola_tangents_with_slope.",
    "For RECTANGULAR HYPERBOLA xy=c^2: use rectangular_hyperbola(c) and rectangular_hyperbola_tangent(c, Point(...)).",
    "For classifying a second degree conic: use conic_classify(Eq(...,0)).",
]

EXAMPLES = [
    'User problem: factor pair of lines x^2 - y^2 = 0\nJSON: {"operation":"evaluate","expression":"pair_lines_separate(Eq(x**2 - y**2, 0))"}',
    'User problem: angle between pair of straight lines x^2 - 3xy + 2y^2 = 0\nJSON: {"operation":"evaluate","expression":"pair_lines_angle_homogeneous(1, -3/2, 2)"}',
    'User problem: properties of parabola y^2 = 12x\nJSON: {"operation":"evaluate","expression":"parabola_properties(3, \'right\')"}',
    'User problem: tangent to y^2=12x at parameter t=2\nJSON: {"operation":"evaluate","expression":"parabola_tangent(3, 2, \'right\')"}',
    'User problem: conic with focus (3,0), directrix x=-3, eccentricity 1\nJSON: {"operation":"evaluate","expression":"conic_from_focus_directrix(Point(3, 0), Eq(x, -3), 1)"}',
    'User problem: ellipse x^2/25 + y^2/9 = 1 properties\nJSON: {"operation":"evaluate","expression":"ellipse_properties(5, 3)"}',
    'User problem: tangent to ellipse x^2/25 + y^2/9 = 1 at (4,9/5)\nJSON: {"operation":"evaluate","expression":"ellipse_tangent(5, 3, Point(4, 9/5))"}',
    'User problem: hyperbola x^2/16 - y^2/9 = 1 properties\nJSON: {"operation":"evaluate","expression":"hyperbola_properties(4, 3)"}',
    'User problem: asymptotes of hyperbola x^2/16 - y^2/9 = 1\nJSON: {"operation":"evaluate","expression":"hyperbola_properties(4, 3)[\'asymptotes\']"}',
    'User problem: tangent to rectangular hyperbola xy=16 at (4,4)\nJSON: {"operation":"evaluate","expression":"rectangular_hyperbola_tangent(4, Point(4, 4))"}',
]

CONIC_MARKERS = (
    "pair_lines_",
    "is_pair_of_lines(",
    "parabola_",
    "ellipse_",
    "hyperbola_",
    "rectangular_hyperbola",
    "conic_classify(",
    "conic_from_focus_directrix(",
    "Ellipse(",
    "Parabola(",
)


def is_conic_expression(expr_str: str) -> bool:
    return any(marker in expr_str for marker in CONIC_MARKERS)


def execute(task: MathTask, expr, variables: list, equations: list):
    if task.operation == "evaluate" and is_conic_expression(task.expression or task.equation or ""):
        if isinstance(expr, (str, bool, dict, sp.Tuple, list)):
            return expr
        try:
            return sp.simplify(expr)
        except Exception:
            return expr
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if not is_conic_expression(expr_str):
        return None

    step_map = [
        ("pair_lines_", "1. Treat the second-degree equation as a pair of straight lines and use the standard pair-line formula."),
        ("is_pair_of_lines(", "1. Check the determinant condition abc + 2fgh - af² - bg² - ch² = 0."),
        ("parabola_standard(", "1. Match the required orientation with y² = ±4ax or x² = ±4ay."),
        ("parabola_properties(", "1. Read the vertex, focus, directrix, axis, and latus rectum from the standard parabola form."),
        ("parabola_point(", "1. Use the parametric point of the parabola."),
        ("parabola_tangent(", "1. Use the tangent form for the selected standard parabola."),
        ("parabola_normal(", "1. Use the normal form for the selected standard parabola."),
        ("parabola_from_focus_directrix(", "1. Use the definition: distance from focus equals distance from directrix."),
        ("conic_from_focus_directrix(", "1. Use the definition: distance from focus = e × distance from directrix."),
        ("ellipse_standard(", "1. Substitute a, b, and the center into the standard ellipse equation."),
        ("ellipse_properties(", "1. Use c² = a² - b² and e = c/a for ellipse properties."),
        ("ellipse_tangent(", "1. Use T = 1 for the tangent to the ellipse at the given point."),
        ("ellipse_normal(", "1. Use the standard normal equation at the point on the ellipse."),
        ("ellipse_tangents_with_slope(", "1. Use y = mx ± √(a²m² + b²), shifted if the center is not the origin."),
        ("hyperbola_standard(", "1. Substitute a, b, and the center into the standard hyperbola equation."),
        ("hyperbola_properties(", "1. Use c² = a² + b² and e = c/a for hyperbola properties."),
        ("rectangular_hyperbola_tangent(", "1. Use T = 0 form: xy₁ + yx₁ = 2c²."),
        ("rectangular_hyperbola(", "1. Use the standard rectangular hyperbola form xy = c²."),
        ("hyperbola_tangents_with_slope(", "1. Use y = mx ± √(a²m² - b²), shifted if the center is not the origin."),
        ("hyperbola_tangent(", "1. Use T = 1 for the tangent to the hyperbola at the given point."),
        ("conic_classify(", "1. Classify by B² - 4AC for Ax² + Bxy + Cy² + Dx + Ey + F = 0."),
    ]

    for marker, first_step in step_map:
        if marker in expr_str:
            lines = [
                first_step,
                "2. Substitute the given values and simplify.",
                "3. The result is:",
                indented_math(result),
            ]
            return "\n".join(lines)

    if any(conic in expr_str for conic in ["Ellipse(", "Parabola("]):
        lines = [
            "1. Define the conic section using its focus, directrix, or axis data.",
            "2. Convert the geometric definition into an algebraic equation.",
            "3. The result is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    return None
