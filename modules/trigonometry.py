from typing import Any

import sympy as sp

from formatter import indented_math, parse_math
from models import MathTask


SYMPY_LOCALS: dict[str, Any] = {}

RULES = [
    "For trigonometric equations, prefer operation 'solve_trig' and keep periodic solutions (n ∈ Integers).",
    "Represent equations explicitly with Eq(..., ...). If user writes sin(x)=1/2, convert to Eq(sin(x), 1/2).",
    "Use trigsimplify for identity simplification and trigexpand for angle-sum/angle-difference expansions.",
]

EXAMPLES = [
    'User problem: solve sin(x) = 1/2\\nJSON: {"operation":"solve_trig","equation":"Eq(sin(x), 1/2)","variable":"x"}',
    'User problem: solve 2*sin(x)**2 - 3*sin(x) + 1 = 0\\nJSON: {"operation":"solve_trig","equation":"Eq(2*sin(x)**2 - 3*sin(x) + 1, 0)","variable":"x"}',
    'User problem: simplify sin(x)**2 + cos(x)**2\\nJSON: {"operation":"trigsimplify","expression":"sin(x)**2 + cos(x)**2"}',
    'User problem: expand sin(a+b)\\nJSON: {"operation":"trigexpand","expression":"sin(a + b)"}',
]

TRIG_FUNCTIONS = (
    sp.sin,
    sp.cos,
    sp.tan,
    sp.cot,
    sp.sec,
    sp.csc,
    sp.asin,
    sp.acos,
    sp.atan,
    sp.acot,
    sp.asec,
    sp.acsc,
)


def _contains_trig(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_trig(item) for item in value)
    if hasattr(value, "has"):
        return bool(value.has(*TRIG_FUNCTIONS))
    return False


def _as_zero_expression(eq_expr: sp.Basic) -> sp.Basic:
    if isinstance(eq_expr, sp.Equality):
        return sp.simplify(eq_expr.lhs - eq_expr.rhs)
    return sp.simplify(eq_expr)


def _dedupe_numeric_roots(roots: list[sp.Expr], tolerance: float = 1e-7) -> list[sp.Expr]:
    ordered = sorted(roots, key=lambda root: float(sp.N(root)))
    unique: list[sp.Expr] = []
    for root in ordered:
        if not unique:
            unique.append(root)
            continue
        if abs(float(sp.N(root - unique[-1]))) > tolerance:
            unique.append(root)
    return [sp.nsimplify(root, [sp.pi]) for root in unique]


def _numeric_real_roots(
    equation: sp.Basic,
    variable: sp.Symbol,
    start: sp.Expr = -2 * sp.pi,
    end: sp.Expr = 2 * sp.pi,
    samples: int = 80,
) -> list[sp.Expr]:
    start_f = float(sp.N(start))
    end_f = float(sp.N(end))
    total_samples = max(samples, 2)
    step = (end_f - start_f) / (total_samples - 1)

    roots: list[sp.Expr] = []
    for idx in range(total_samples):
        guess = start_f + idx * step
        try:
            candidate = sp.nsolve(equation, variable, guess, tol=1e-14, maxsteps=80, prec=50)
        except Exception:
            continue

        approx = sp.N(candidate)
        real_part, imag_part = approx.as_real_imag()
        if abs(float(sp.N(imag_part))) > 1e-8:
            continue

        root = sp.N(real_part, 15)
        root_f = float(root)
        if root_f < start_f - 1e-6 or root_f > end_f + 1e-6:
            continue
        roots.append(root)

    return _dedupe_numeric_roots(roots)


def _solve_single_equation(equation: sp.Basic, variable: sp.Symbol):
    real_solution = sp.solveset(equation, variable, domain=sp.S.Reals)
    if real_solution == sp.EmptySet:
        complex_solution = sp.solveset(equation, variable, domain=sp.S.Complexes)
        return complex_solution if complex_solution != sp.EmptySet else real_solution

    if isinstance(real_solution, sp.ConditionSet):
        fallback = sp.solve(sp.Eq(equation, 0), variable)
        if fallback:
            return sp.FiniteSet(*fallback)

        numeric_roots = _numeric_real_roots(equation, variable)
        if numeric_roots:
            return sp.FiniteSet(*numeric_roots)

    return real_solution


def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if isinstance(expr, list):
        if not expr:
            return None
        expr = expr[0]

    targets = equations if equations else [expr]
    has_trig = any(_contains_trig(target) for target in targets)

    if task.operation in {"trigsimplify", "trig_simplify"}:
        return sp.trigsimp(sp.simplify(expr))

    if task.operation == "trigexpand":
        return sp.expand_trig(expr)

    if task.operation in {"trigreduce", "trig_reduce"}:
        return sp.trigsimp(sp.expand_trig(expr))

    if task.operation == "evaluate" and has_trig:
        return sp.trigsimp(sp.simplify(expr))

    if task.operation not in {"solve", "solve_trig"}:
        return None
    if task.operation == "solve" and not has_trig:
        return None

    canonical_equations = [_as_zero_expression(target) for target in targets]
    solve_variables = list(variables)
    if not solve_variables:
        all_symbols: set[sp.Symbol] = set()
        for equation in canonical_equations:
            all_symbols.update(equation.free_symbols)
        solve_variables = sorted(all_symbols, key=lambda symbol: symbol.name)
        if not solve_variables:
            solve_variables = [sp.Symbol(task.variable or "x")]

    if len(canonical_equations) > 1 or len(solve_variables) > 1:
        return sp.nonlinsolve(canonical_equations, solve_variables)

    return _solve_single_equation(canonical_equations[0], solve_variables[0])


def _solution_label(result: Any) -> str:
    if isinstance(result, sp.ConditionSet):
        return "3. Closed-form symbolic reduction is incomplete, so SymPy returned an implicit condition set:"
    if result == sp.EmptySet:
        return "3. No solution exists in the selected domain:"
    if isinstance(result, sp.FiniteSet):
        return "3. Discrete solution set:"
    if isinstance(result, (sp.ImageSet, sp.Union)):
        return "3. General periodic solution family:"
    return "3. Solution set:"


def get_steps(task: MathTask, expr_str: str, result: Any):
    from modules import get_all_locals

    if task.operation not in {
        "solve",
        "solve_trig",
        "trigsimplify",
        "trig_simplify",
        "trigexpand",
        "trigreduce",
        "trig_reduce",
        "evaluate",
    }:
        return None

    locals_dict = get_all_locals()
    lines: list[str] = []

    if task.operation in {"solve", "solve_trig"}:
        equation_texts = task.equations or ([expr_str] if expr_str else [])
        if not equation_texts:
            return None

        parsed_equations: list[sp.Basic] = []
        for equation_text in equation_texts:
            parsed = parse_math(equation_text, locals_dict)
            if isinstance(parsed, (list, tuple)) and parsed:
                parsed = parsed[0]
            parsed_equations.append(_as_zero_expression(parsed))

        if task.operation == "solve" and not any(_contains_trig(eq) for eq in parsed_equations):
            return None

        lines.append("1. Rewrite each trigonometric equation in standard form:")
        for equation in parsed_equations:
            lines.append(indented_math(sp.Eq(equation, 0)))

        variable_names = task.variables or ([task.variable] if task.variable else ["x"])
        if len(parsed_equations) > 1 or len(variable_names) > 1:
            lines.append("2. Solve the nonlinear system while preserving valid trigonometric constraints.")
        else:
            lines.append(
                f"2. Solve for {variable_names[0]} over the real domain and keep periodic solution families."
            )

        lines.append(_solution_label(result))
        lines.append(indented_math(result))
        return "\n".join(lines)

    parsed_expr = parse_math(expr_str, locals_dict)
    if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
        parsed_expr = parsed_expr[0]

    if task.operation == "evaluate" and not _contains_trig(parsed_expr):
        return None

    if task.operation in {"trigsimplify", "trig_simplify", "evaluate"}:
        lines.extend(
            [
                "1. Start with the trigonometric expression:",
                indented_math(parsed_expr),
                "2. Apply trigonometric identities and simplify algebraically.",
                "3. Simplified result:",
                indented_math(result),
            ]
        )
        return "\n".join(lines)

    if task.operation == "trigexpand":
        lines.extend(
            [
                "1. Start with the trigonometric expression:",
                indented_math(parsed_expr),
                "2. Apply angle addition/subtraction identities to expand compound angles.",
                "3. Expanded result:",
                indented_math(result),
            ]
        )
        return "\n".join(lines)

    if task.operation in {"trigreduce", "trig_reduce"}:
        lines.extend(
            [
                "1. Start with the trigonometric expression:",
                indented_math(parsed_expr),
                "2. Expand then simplify using standard identities to reduce the form.",
                "3. Reduced result:",
                indented_math(result),
            ]
        )
        return "\n".join(lines)

    return None
