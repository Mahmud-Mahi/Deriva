from typing import Any

import sympy as sp

from formatter import indented_math, parse_math
from models import MathTask


x, y, z = sp.symbols("x y z")


def _as_expr(eq_or_expr):
    if isinstance(eq_or_expr, sp.Equality):
        return sp.expand(eq_or_expr.lhs - eq_or_expr.rhs)
    return sp.sympify(eq_or_expr)


def _as_relation(value):
    if isinstance(value, (sp.Equality, sp.StrictLessThan, sp.StrictGreaterThan, sp.LessThan, sp.GreaterThan)):
        return value
    return sp.Eq(value, 0, evaluate=False)


def _relation_boundary(relation):
    relation = _as_relation(relation)
    return sp.Eq(relation.lhs, relation.rhs, evaluate=False)


def _relation_holds(relation, substitutions) -> bool:
    relation = _as_relation(relation)
    value = relation.subs(substitutions)
    try:
        return bool(value)
    except TypeError:
        return bool(sp.simplify(value))


# --- Polynomial And Equation Tools ---


def solve_equation(equation, variable=x, domain="complex"):
    expr = _as_expr(equation)
    if domain == "real":
        return sp.solveset(expr, variable, domain=sp.S.Reals)
    if domain == "integer":
        return sp.solveset(expr, variable, domain=sp.S.Integers)
    return sp.solveset(expr, variable, domain=sp.S.Complexes)


def solve_algebraic(equation, variable=x):
    return sp.Tuple(*sp.solve(_as_relation(equation), variable))


def polynomial_roots(poly_expr, variable=x):
    return sp.roots(_as_expr(poly_expr), variable)


def polynomial_nroots(poly_expr, variable=x):
    return sp.Tuple(*sp.nroots(_as_expr(poly_expr), n=15, maxsteps=100))


def polynomial_factor(poly_expr):
    return sp.factor(_as_expr(poly_expr))


def polynomial_expand(poly_expr):
    return sp.expand(poly_expr)


def polynomial_degree(poly_expr, variable=x):
    return sp.Poly(_as_expr(poly_expr), variable).degree()


def polynomial_coefficients(poly_expr, variable=x):
    return sp.Tuple(*sp.Poly(_as_expr(poly_expr), variable).all_coeffs())


def polynomial_discriminant(poly_expr, variable=x):
    return sp.discriminant(_as_expr(poly_expr), variable)


def quadratic_nature(a, b, c):
    delta = sp.simplify(b**2 - 4 * a * c)
    if delta.is_positive:
        nature = "two distinct real roots"
    elif delta == 0:
        nature = "two equal real roots"
    elif delta.is_negative:
        nature = "complex conjugate roots"
    else:
        nature = "depends on parameter"
    return {"discriminant": delta, "nature": nature}


def vieta_relations(poly_expr, variable=x):
    poly = sp.Poly(_as_expr(poly_expr), variable)
    roots = sp.symbols(f"r1:{poly.degree() + 1}")
    coeffs = poly.all_coeffs()
    monic_coeffs = [sp.simplify(coeff / coeffs[0]) for coeff in coeffs]
    relations = {}
    for k in range(1, poly.degree() + 1):
        symmetric_sum = sum(sp.prod(combo) for combo in __import__("itertools").combinations(roots, k))
        relations[str(symmetric_sum)] = sp.simplify((-1) ** k * monic_coeffs[k])
    return relations


def polynomial_division(dividend, divisor, variable=x):
    q, r = sp.div(_as_expr(dividend), _as_expr(divisor), variable)
    return {"quotient": q, "remainder": r}


def remainder_theorem(poly_expr, value, variable=x):
    return sp.simplify(_as_expr(poly_expr).subs(variable, value))


def factor_theorem(poly_expr, value, variable=x):
    return remainder_theorem(poly_expr, value, variable) == 0


def polynomial_gcd(poly1, poly2, variable=x):
    return sp.gcd(_as_expr(poly1), _as_expr(poly2))


def polynomial_lcm(poly1, poly2, variable=x):
    return sp.lcm(_as_expr(poly1), _as_expr(poly2))


def rational_simplify(expr):
    return sp.cancel(sp.factor(expr))


def partial_fractions(expr, variable=x):
    return sp.apart(expr, variable)


def solve_system(equations, variables):
    return sp.solve([_as_relation(eq) for eq in equations], variables, dict=True)


def solve_linear_system(equations, variables):
    return sp.linsolve([_as_relation(eq) for eq in equations], variables)


def solve_non_linear_system(equations, variables):
    exprs = [_as_expr(eq) for eq in equations]
    return sp.nonlinsolve(exprs, variables)


def solve_radical_equation(equation, variable=x):
    return sp.Tuple(*sp.solve(_as_relation(equation), variable, check=True))


def solve_exponential_equation(equation, variable=x):
    return sp.Tuple(*sp.solve(_as_relation(equation), variable, check=True))


def solve_log_equation(equation, variable=x):
    return sp.Tuple(*sp.solve(_as_relation(equation), variable, check=True))


# --- Inequalities ---


def solve_inequality(inequality, variable=x, domain=sp.S.Reals):
    return sp.reduce_inequalities([inequality], variable)


def solve_inequalities(inequalities, variables=None):
    if variables is None:
        variables = sorted(set().union(*(getattr(ineq, "free_symbols", set()) for ineq in inequalities)), key=lambda s: s.name)
    return sp.reduce_inequalities(inequalities, variables)


def solve_polynomial_inequality(poly_expr, relation=">=", variable=x):
    expr = _as_expr(poly_expr)
    relational = {
        ">": expr > 0,
        ">=": expr >= 0,
        "<": expr < 0,
        "<=": expr <= 0,
    }[relation]
    return sp.solve_univariate_inequality(relational, variable)


def solve_rational_inequality(numerator, denominator, relation=">=", variable=x):
    expr = sp.cancel(_as_expr(numerator) / _as_expr(denominator))
    relational = {
        ">": expr > 0,
        ">=": expr >= 0,
        "<": expr < 0,
        "<=": expr <= 0,
    }[relation]
    return sp.solve_univariate_inequality(relational, variable)


def solve_abs_inequality(expr, relation, bound, variable=x):
    abs_expr = sp.Abs(expr)
    relational = {
        ">": abs_expr > bound,
        ">=": abs_expr >= bound,
        "<": abs_expr < bound,
        "<=": abs_expr <= bound,
    }[relation]
    return sp.reduce_inequalities([relational], variable)


def sign_chart(poly_expr, variable=x):
    expr = _as_expr(poly_expr)
    roots = sorted([root for root in sp.solve(expr, variable) if root.is_real], key=lambda r: float(sp.N(r)))
    points = [-sp.oo, *roots, sp.oo]
    intervals = []
    for left, right in zip(points, points[1:]):
        if left == -sp.oo:
            test = roots[0] - 1 if roots else 0
        elif right == sp.oo:
            test = roots[-1] + 1 if roots else 0
        else:
            test = (left + right) / 2
        value = sp.simplify(expr.subs(variable, test))
        intervals.append({"interval": sp.Interval.open(left, right), "sign": sp.sign(value)})
    return {"roots": sp.Tuple(*roots), "intervals": intervals}


# --- Sequences, Series, And Algebraic Expressions ---


def arithmetic_progression_nth(a, d, n):
    return sp.simplify(a + (n - 1) * d)


def arithmetic_progression_sum(a, d, n):
    return sp.simplify(n * (2 * a + (n - 1) * d) / 2)


def geometric_progression_nth(a, r, n):
    return sp.simplify(a * r ** (n - 1))


def geometric_progression_sum(a, r, n):
    if sp.simplify(r - 1) == 0:
        return sp.simplify(a * n)
    return sp.simplify(a * (r**n - 1) / (r - 1))


def geometric_progression_infinite_sum(a, r):
    return sp.simplify(a / (1 - r))


def sum_natural(n):
    return sp.simplify(n * (n + 1) / 2)


def sum_squares(n):
    return sp.simplify(n * (n + 1) * (2 * n + 1) / 6)


def sum_cubes(n):
    return sp.simplify((n * (n + 1) / 2) ** 2)


# --- Linear Programming ---


def linear_program_vertices(constraints, variables=(x, y)):
    vx, vy = variables
    relations = [_as_relation(constraint) for constraint in constraints]
    boundaries = [_relation_boundary(relation) for relation in relations]
    candidates = []

    for i in range(len(boundaries)):
        for j in range(i + 1, len(boundaries)):
            solution = sp.solve([boundaries[i], boundaries[j]], [vx, vy], dict=True)
            for sol in solution:
                if vx in sol and vy in sol:
                    point = (sp.simplify(sol[vx]), sp.simplify(sol[vy]))
                    if all(_relation_holds(relation, {vx: point[0], vy: point[1]}) for relation in relations):
                        candidates.append(point)

    unique = []
    for point in candidates:
        if point not in unique:
            unique.append(point)
    return sp.Tuple(*unique)


def linear_program_evaluate(objective, vertices, variables=(x, y)):
    vx, vy = variables
    return sp.Tuple(*(
        sp.Tuple(point[0], point[1], sp.simplify(objective.subs({vx: point[0], vy: point[1]})))
        for point in vertices
    ))


def linear_program_optimize(objective, constraints, variables=(x, y), goal="max"):
    vertices = linear_program_vertices(constraints, variables)
    values = linear_program_evaluate(objective, vertices, variables)
    if not values:
        return {"vertices": vertices, "status": "no bounded feasible vertex found"}
    key = lambda row: sp.N(row[2])
    best = max(values, key=key) if goal == "max" else min(values, key=key)
    return {"vertices": vertices, "values": values, "optimum": best, "goal": goal}


def linear_program_maximize(objective, constraints, variables=(x, y)):
    return linear_program_optimize(objective, constraints, variables, "max")


def linear_program_minimize(objective, constraints, variables=(x, y)):
    return linear_program_optimize(objective, constraints, variables, "min")


SYMPY_LOCALS = {
    "x": x,
    "y": y,
    "z": z,
    "solve_equation": solve_equation,
    "solve_algebraic": solve_algebraic,
    "polynomial_roots": polynomial_roots,
    "polynomial_nroots": polynomial_nroots,
    "polynomial_factor": polynomial_factor,
    "polynomial_expand": polynomial_expand,
    "polynomial_degree": polynomial_degree,
    "polynomial_coefficients": polynomial_coefficients,
    "polynomial_discriminant": polynomial_discriminant,
    "quadratic_nature": quadratic_nature,
    "vieta_relations": vieta_relations,
    "polynomial_division": polynomial_division,
    "remainder_theorem": remainder_theorem,
    "factor_theorem": factor_theorem,
    "polynomial_gcd": polynomial_gcd,
    "polynomial_lcm": polynomial_lcm,
    "rational_simplify": rational_simplify,
    "partial_fractions": partial_fractions,
    "solve_system": solve_system,
    "solve_linear_system": solve_linear_system,
    "solve_non_linear_system": solve_non_linear_system,
    "solve_radical_equation": solve_radical_equation,
    "solve_exponential_equation": solve_exponential_equation,
    "solve_log_equation": solve_log_equation,
    "solve_inequality": solve_inequality,
    "solve_inequalities": solve_inequalities,
    "solve_polynomial_inequality": solve_polynomial_inequality,
    "solve_rational_inequality": solve_rational_inequality,
    "solve_abs_inequality": solve_abs_inequality,
    "sign_chart": sign_chart,
    "arithmetic_progression_nth": arithmetic_progression_nth,
    "arithmetic_progression_sum": arithmetic_progression_sum,
    "geometric_progression_nth": geometric_progression_nth,
    "geometric_progression_sum": geometric_progression_sum,
    "geometric_progression_infinite_sum": geometric_progression_infinite_sum,
    "sum_natural": sum_natural,
    "sum_squares": sum_squares,
    "sum_cubes": sum_cubes,
    "linear_program_vertices": linear_program_vertices,
    "linear_program_evaluate": linear_program_evaluate,
    "linear_program_optimize": linear_program_optimize,
    "linear_program_maximize": linear_program_maximize,
    "linear_program_minimize": linear_program_minimize,
}

RULES = [
    "Use ** for powers, not ^.",
    "For polynomial equations: use solve_equation(Eq(...,0), x), solve_algebraic(...), polynomial_roots(...), polynomial_factor(...), polynomial_discriminant(...), or quadratic_nature(a,b,c).",
    "For Vieta/root coefficient problems: use vieta_relations(poly, x).",
    "For polynomial division/remainder/factor theorem: use polynomial_division(dividend, divisor), remainder_theorem(poly, value), or factor_theorem(poly, value).",
    "For rational expressions: use rational_simplify(expr) or partial_fractions(expr, x).",
    "For systems: use solve_system([...], [x,y]), solve_linear_system([...], [x,y]), or solve_non_linear_system([...], [x,y]).",
    "For inequalities: use solve_inequality(ineq, x), solve_inequalities([...], [x,y]), solve_polynomial_inequality(expr, relation, x), solve_rational_inequality(num, den, relation, x), solve_abs_inequality(expr, relation, bound, x), or sign_chart(expr, x).",
    "For AP/GP and sums: use arithmetic_progression_nth/sum, geometric_progression_nth/sum/infinite_sum, sum_natural, sum_squares, sum_cubes.",
    "For 2-variable linear programming: use linear_program_maximize(objective, [constraints], (x,y)) or linear_program_minimize(...). Include boundary constraints like x>=0, y>=0.",
]

EXAMPLES = [
    'User problem: solve x^3 - 6x^2 + 11x - 6 = 0\nJSON: {"operation":"evaluate","expression":"polynomial_roots(x**3 - 6*x**2 + 11*x - 6, x)"}',
    'User problem: nature of roots of 2x^2 - 4x + 3\nJSON: {"operation":"evaluate","expression":"quadratic_nature(2, -4, 3)"}',
    'User problem: solve inequality x^2 - 5x + 6 >= 0\nJSON: {"operation":"evaluate","expression":"solve_polynomial_inequality(x**2 - 5*x + 6, \'>=\', x)"}',
    'User problem: solve rational inequality (x-1)/(x+2) > 0\nJSON: {"operation":"evaluate","expression":"solve_rational_inequality(x - 1, x + 2, \'>\', x)"}',
    'User problem: solve |x-2| <= 5\nJSON: {"operation":"evaluate","expression":"solve_abs_inequality(x - 2, \'<=\', 5, x)"}',
    'User problem: solve system x+y=5, x-y=1\nJSON: {"operation":"evaluate","expression":"solve_system([Eq(x + y, 5), Eq(x - y, 1)], [x, y])"}',
    'User problem: maximize 3x+2y subject to x+y<=4, x<=2, y<=3, x>=0, y>=0\nJSON: {"operation":"evaluate","expression":"linear_program_maximize(3*x + 2*y, [x + y <= 4, x <= 2, y <= 3, x >= 0, y >= 0], (x, y))"}',
]

ALGEBRA_MARKERS = (
    "solve_equation(",
    "solve_algebraic(",
    "polynomial_",
    "quadratic_nature(",
    "vieta_relations(",
    "remainder_theorem(",
    "factor_theorem(",
    "rational_simplify(",
    "partial_fractions(",
    "solve_system(",
    "solve_linear_system(",
    "solve_non_linear_system(",
    "solve_radical_equation(",
    "solve_exponential_equation(",
    "solve_log_equation(",
    "solve_inequality(",
    "solve_inequalities(",
    "solve_rational_inequality(",
    "solve_abs_inequality(",
    "sign_chart(",
    "arithmetic_progression_",
    "geometric_progression_",
    "sum_natural(",
    "sum_squares(",
    "sum_cubes(",
    "linear_program_",
)


def is_algebra_task(task: MathTask, expr_str: str | None = None) -> bool:
    text = expr_str if expr_str is not None else (task.expression or task.equation or "")
    return any(marker in text for marker in ALGEBRA_MARKERS)


def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if task.operation == "evaluate" and is_algebra_task(task):
        return expr
    if task.operation == "solve":
        return sp.solve(equations if equations else [expr], variables, dict=len(variables) > 1)
    if task.operation == "simplify":
        return sp.simplify(expr)
    if task.operation == "factor":
        return sp.factor(expr)
    if task.operation == "expand":
        return sp.expand(expr)
    return None


def get_poly_details(eq_expr: sp.Basic, var: sp.Symbol):
    try:
        poly_expr = eq_expr.lhs - eq_expr.rhs if isinstance(eq_expr, sp.Equality) else eq_expr
        poly = sp.Poly(poly_expr, var)
        return poly, poly.degree(), poly.all_coeffs()
    except Exception:
        return None, None, None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if task.operation == "evaluate" and is_algebra_task(task, expr_str):
        step_map = [
            ("linear_program_", "1. Find feasible corner points from the constraint boundary lines."),
            ("solve_equation(", "1. Move all terms to one side and solve over the requested domain."),
            ("solve_algebraic(", "1. Use algebraic transformations and solve for the requested variable."),
            ("solve_inequalities(", "1. Combine all inequalities and reduce the feasible set."),
            ("solve_inequality(", "1. Move all terms to one side and solve the inequality over the real line."),
            ("solve_polynomial_inequality(", "1. Find critical roots, then test signs across intervals."),
            ("solve_rational_inequality(", "1. Find zeros and excluded denominator points, then test signs."),
            ("solve_abs_inequality(", "1. Split or reduce the absolute value inequality."),
            ("sign_chart(", "1. Find real roots and test the sign on each interval."),
            ("polynomial_roots(", "1. Factor or solve the polynomial equation."),
            ("polynomial_nroots(", "1. Use numerical root approximation for the polynomial."),
            ("polynomial_factor(", "1. Factor using algebraic identities and root information."),
            ("polynomial_degree(", "1. Find the highest power of the variable with non-zero coefficient."),
            ("polynomial_division(", "1. Divide the polynomial by the divisor."),
            ("polynomial_discriminant(", "1. Compute the discriminant to study repeated roots/root nature."),
            ("polynomial_coefficients(", "1. Arrange the polynomial in descending powers and read coefficients."),
            ("polynomial_gcd(", "1. Factor both polynomials and keep the common factors with minimum powers."),
            ("polynomial_lcm(", "1. Factor both polynomials and keep all factors with maximum powers."),
            ("quadratic_nature(", "1. Use Δ = b² - 4ac to determine the root nature."),
            ("vieta_relations(", "1. Compare coefficients with the monic polynomial to get root relations."),
            ("remainder_theorem(", "1. Substitute the given value into the polynomial."),
            ("factor_theorem(", "1. Use the remainder theorem; zero remainder means it is a factor."),
            ("rational_simplify(", "1. Factor numerator and denominator, then cancel common factors."),
            ("partial_fractions(", "1. Decompose the rational expression into simpler fractions."),
            ("solve_system(", "1. Solve the equations simultaneously."),
            ("solve_linear_system(", "1. Treat the equations as a linear system."),
            ("solve_non_linear_system(", "1. Solve the nonlinear equations simultaneously."),
            ("solve_radical_equation(", "1. Isolate radicals carefully and check for extraneous roots."),
            ("solve_exponential_equation(", "1. Rewrite exponential terms with compatible bases or use logs."),
            ("solve_log_equation(", "1. Use logarithm rules and check domain restrictions."),
            ("arithmetic_progression_", "1. Use the standard AP formula."),
            ("geometric_progression_", "1. Use the standard GP formula."),
            ("sum_natural(", "1. Use n(n+1)/2."),
            ("sum_squares(", "1. Use n(n+1)(2n+1)/6."),
            ("sum_cubes(", "1. Use [n(n+1)/2]²."),
        ]
        for marker, first_step in step_map:
            if marker in expr_str:
                return "\n".join([
                    first_step,
                    "2. Substitute the given values and simplify.",
                    "3. The result is:",
                    indented_math(result),
                ])

    from modules import get_all_locals
    locals_dict = get_all_locals()
    lines = []

    if task.operation == "solve":
        if task.equations and len(task.equations) > 1:
            lines.append("1. Identify the system of equations:")
            for eq in task.equations:
                lines.append(indented_math(eq))
            lines.append(f"2. Solve the system for variables: {', '.join(task.variables or [task.variable])}.")
            lines.append("3. The solution set is:")
            lines.append(indented_math(result))
            return "\n".join(lines)

        expr = parse_math(expr_str, locals_dict)
        var = sp.Symbol(task.variable) if task.variable else sp.Symbol("x")
        poly, degree, coeffs = get_poly_details(expr, var)
        lines.append("1. Write the equation in standard form:")
        lines.append(indented_math(expr))

        if degree == 2 and len(coeffs) == 3:
            a, b, c = coeffs
            delta = b**2 - 4 * a * c
            lines.append(f"2. This is quadratic with a={a}, b={b}, c={c}.")
            lines.append("3. Compute the discriminant:")
            lines.append(indented_math(sp.Eq(sp.Symbol("Δ"), delta)))
            lines.append("4. Apply the quadratic formula.")
        elif degree is not None and degree > 2:
            lines.append(f"2. This is a polynomial equation of degree {degree}.")
            lines.append("3. Use factorization, substitution, or root theorems.")
        else:
            lines.append(f"2. Isolate the variable {var} using algebraic transformations.")

        lines.append(f"Final solution for {var}:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    if task.operation == "factor":
        return "\n".join([
            "1. Start with the expression:",
            indented_math(expr_str),
            "2. Apply identities, grouping, or root information.",
            "3. The factored form is:",
            indented_math(result),
        ])

    if task.operation == "simplify":
        return "\n".join([
            "1. Start with the expression:",
            indented_math(expr_str),
            "2. Combine like terms, cancel common factors, and apply identities.",
            "3. The simplified result is:",
            indented_math(result),
        ])

    return None
