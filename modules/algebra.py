import sympy as sp
from typing import Any
from models import MathTask
from formatter import indented_math, pretty_math, parse_math

SYMPY_LOCALS = {}
RULES = [
    "Use ** for powers, not ^.",
    "Preserve square roots exactly: sqrt(25 - x**2) must not become sqrt(25 - x**2)**2.",
    "For standard operations use solve, simplify, factor, or expand."
]
EXAMPLES = [
    'User problem: solve x**2 - 5*x + 6 = 0\nJSON: {"operation":"solve","equation":"Eq(x**2 - 5*x + 6, 0)","variable":"x"}',
    'User problem: factor x**2 - 9\nJSON: {"operation":"factor","expression":"x**2 - 9"}'
]

def get_poly_details(eq_expr: sp.Basic, var: sp.Symbol):
    """Helper to analyze polynomial properties for step generation."""
    try:
        # Move everything to one side: lhs - rhs = 0
        if isinstance(eq_expr, sp.Equality):
            poly_expr = eq_expr.lhs - eq_expr.rhs
        else:
            poly_expr = eq_expr
            
        poly = sp.Poly(poly_expr, var)
        degree = poly.degree()
        coeffs = poly.all_coeffs()
        return poly, degree, coeffs
    except:
        return None, None, None

def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if task.operation == "solve": 
        # Handle systems or single equations
        return sp.solve(equations if equations else [expr], variables, dict=len(variables) > 1)
    if task.operation == "simplify": return sp.simplify(expr)
    if task.operation == "factor": return sp.factor(expr)
    if task.operation == "expand": return sp.expand(expr)
    return None

def get_steps(task: MathTask, expr_str: str, result: Any):
    from modules import get_all_locals
    locals_dict = get_all_locals()
    lines = []
    
    if task.operation == "solve":
        # Handle System of Equations
        if task.equations and len(task.equations) > 1:
            lines.append("1. Identify the system of equations:")
            for eq in task.equations:
                lines.append(indented_math(eq))
            lines.append(f"2. Solve the system for variables: {', '.join(task.variables)}.")
            lines.append("3. The solution set is:")
            lines.append(indented_math(result))
            return "\n".join(lines)

        # Handle Single Polynomial Equation
        expr = parse_math(expr_str, locals_dict)
        var = sp.Symbol(task.variable) if task.variable else sp.Symbol('x')
        poly, degree, coeffs = get_poly_details(expr, var)

        lines.append("1. Write the equation in standard form:")
        lines.append(indented_math(expr))

        if degree == 2 and len(coeffs) == 3:
            a, b, c = coeffs
            delta = b**2 - 4*a*c
            lines.append(f"2. This is a quadratic equation where a={a}, b={b}, c={c}.")
            lines.append(f"3. Calculate the discriminant (Δ = b² - 4ac):")
            lines.append(indented_math(sp.Eq(sp.Symbol("Δ"), delta)))
            if delta > 0:
                lines.append("   Since Δ > 0, there are two distinct real roots.")
            elif delta == 0:
                lines.append("   Since Δ = 0, there is one repeated real root.")
            else:
                lines.append("   Since Δ < 0, the roots are complex.")
            lines.append("4. Apply the quadratic formula: x = [-b ± √Δ] / 2a")

        elif degree is not None and degree > 2:
            lines.append(f"2. This is a polynomial equation of degree {degree}.")
            lines.append("3. Use the Rational Root Theorem or factorization to find the roots.")
        
        else:
            lines.append(f"2. Isolate the variable {var} using algebraic transformations.")

        lines.append(f"Final Solution for {var}:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    if task.operation == "factor":
        lines.append("1. Start with the expression:")
        lines.append(indented_math(expr_str))
        lines.append("2. Look for common factors, use binomial patterns (like a²-b²),")
        lines.append("   or find roots to rewrite as a product of linear/quadratic factors.")
        lines.append("3. The factored form is:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    if task.operation == "simplify":
        lines.append("1. Original expression:")
        lines.append(indented_math(expr_str))
        lines.append("2. Combine like terms, reduce fractions, and apply algebraic identities.")
        lines.append("3. The simplified result is:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    return None