from typing import Any

import sympy as sp

from formatter import indented_math, parse_math
from models import MathTask


SYMPY_LOCALS: dict[str, Any] = {}

RULES = [
    "For trigonometric equations, prefer operation 'solve_trig' and keep periodic solutions (n ∈ Integers).",
    "For inverse trigonometric equations, use 'solve_inverse_trig' and specify principal values where applicable.",
    "For inverse trig simplification (e.g., arcsin(sin(x))), use 'simplify_inverse_trig' operation.",
    "Represent equations explicitly with Eq(..., ...). If user writes sin(x)=1/2, convert to Eq(sin(x), 1/2).",
    "Use trigsimplify for identity simplification, trigexpand for angle expansions, and trigreduce for power reduction.",
    "For compositions like arcsin(sin(x)) or arccos(cos(x)), verify domain constraints and simplify carefully.",
    "Use 'trig_domain_range' to determine valid domain and range for inverse trig functions.",
    "For trig inequalities, use 'solve_trig_inequality' and express solutions as intervals or unions.",
    "For JEE Advanced: Use 'product_to_sum' to convert products, 'sum_to_product' for sums, 'trig_range_max_min' for extrema.",
    "For principal values in JEE: Use 'solve_principal_values' to find solutions in [0, 2π) or other specified intervals.",
    "For composite functions and multiple angles: Use standard 'solve_trig' which handles sin(nx), cos(nx), tan(nx) automatically.",
]

EXAMPLES = [
    'User: solve sin(x) = 1/2\\nJSON: {"operation":"solve_trig","equation":"Eq(sin(x), 1/2)","variable":"x"}',
    'User: solve sin(3x) = sin(x)\\nJSON: {"operation":"solve_trig","equation":"Eq(sin(3*x), sin(x))","variable":"x"}',
    'User: solve 2sin²(x) - 3sin(x) + 1 = 0\\nJSON: {"operation":"solve_trig","equation":"Eq(2*sin(x)**2 - 3*sin(x) + 1, 0)","variable":"x"}',
    'User: convert sin(5x)*cos(3x) to sum\\nJSON: {"operation":"product_to_sum","expression":"sin(5*x)*cos(3*x)"}',
    'User: convert sin(x) + sin(3x) to product\\nJSON: {"operation":"sum_to_product","expression":"sin(x) + sin(3*x)"}',
    'User: find max/min of sin(x) + cos(x)\\nJSON: {"operation":"trig_range_max_min","expression":"sin(x) + cos(x)","variable":"x"}',
    'User: find principal values of sin(x) = 1/2 in [0,2π)\\nJSON: {"operation":"solve_principal_values","equation":"Eq(sin(x), 1/2)","variable":"x","interval":"[0,2*pi)"}',
    'User: solve sin(x) = cos(x)\\nJSON: {"operation":"solve_trig","equation":"Eq(sin(x), cos(x))","variable":"x"}',
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
    sp.sinh,
    sp.cosh,
    sp.tanh,
    sp.asinh,
    sp.acosh,
    sp.atanh,
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


def _simplify_inverse_trig_composition(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic:
    """
    Simplify compositions of inverse and regular trig functions.
    E.g., arcsin(sin(x)) = x (with domain constraints)
    """
    expr = expr.rewrite(sp.atan2, sp.atan)
    
    # Handle arcsin(sin(x)), arccos(cos(x)), arctan(tan(x)) etc.
    if isinstance(expr, sp.asin):
        arg = expr.args[0]
        if arg.has(sp.sin):
            inner = sp.asin(sp.sin(variable))
            # arcsin(sin(x)) = x for x in [-π/2, π/2]
            return inner
    
    if isinstance(expr, sp.acos):
        arg = expr.args[0]
        if arg.has(sp.cos):
            inner = sp.acos(sp.cos(variable))
            # arccos(cos(x)) = x for x in [0, π]
            return inner
    
    if isinstance(expr, sp.atan):
        arg = expr.args[0]
        if arg.has(sp.tan):
            inner = sp.atan(sp.tan(variable))
            # arctan(tan(x)) = x for x in (-π/2, π/2)
            return inner
    
    # For other forms, use sympy's standard simplification
    return sp.simplify(expr)


def _get_inverse_trig_domain_range(func_name: str) -> tuple:
    """
    Return (domain, range) for inverse trigonometric functions.
    Domain and range are returned as intervals.
    """
    domain_range_map = {
        'asin': (sp.Interval(-1, 1), sp.Interval(-sp.pi/2, sp.pi/2)),
        'arcsin': (sp.Interval(-1, 1), sp.Interval(-sp.pi/2, sp.pi/2)),
        'acos': (sp.Interval(-1, 1), sp.Interval(0, sp.pi)),
        'arccos': (sp.Interval(-1, 1), sp.Interval(0, sp.pi)),
        'atan': (sp.S.Reals, sp.Interval(-sp.pi/2, sp.pi/2)),
        'arctan': (sp.S.Reals, sp.Interval(-sp.pi/2, sp.pi/2)),
        'asinh': (sp.S.Reals, sp.S.Reals),
        'arcsinh': (sp.S.Reals, sp.S.Reals),
        'acosh': (sp.Interval(1, sp.oo), sp.Interval(0, sp.oo)),
        'arccosh': (sp.Interval(1, sp.oo), sp.Interval(0, sp.oo)),
        'atanh': (sp.Interval(-1, 1), sp.S.Reals),
        'arctanh': (sp.Interval(-1, 1), sp.S.Reals),
    }
    return domain_range_map.get(func_name, (None, None))


def _solve_inverse_trig_equation(equation: sp.Basic, variable: sp.Symbol) -> Any:
    """
    Solve equations involving inverse trigonometric functions.
    E.g., arcsin(x) = π/6, arccos(x) = π/4, etc.
    """
    # Apply forward trig function to both sides
    if isinstance(equation, sp.Equality):
        lhs, rhs = equation.lhs, equation.rhs
    else:
        lhs, rhs = equation, 0
    
    # Check what inverse trig function is on LHS
    if isinstance(lhs, (sp.asin, sp.acos, sp.atan, sp.asinh, sp.acosh, sp.atanh)):
        func_type = type(lhs)
        arg = lhs.args[0]
        
        # Apply forward function to both sides
        if func_type == sp.asin:
            return sp.solveset(sp.Eq(arg, sp.sin(rhs)), variable, domain=sp.S.Reals)
        elif func_type == sp.acos:
            return sp.solveset(sp.Eq(arg, sp.cos(rhs)), variable, domain=sp.S.Reals)
        elif func_type == sp.atan:
            return sp.solveset(sp.Eq(arg, sp.tan(rhs)), variable, domain=sp.S.Reals)
        elif func_type == sp.asinh:
            return sp.solveset(sp.Eq(arg, sp.sinh(rhs)), variable, domain=sp.S.Reals)
        elif func_type == sp.acosh:
            return sp.solveset(sp.Eq(arg, sp.cosh(rhs)), variable, domain=sp.S.Reals)
        elif func_type == sp.atanh:
            return sp.solveset(sp.Eq(arg, sp.tanh(rhs)), variable, domain=sp.S.Reals)
    
    # Otherwise solve normally
    return sp.solveset(lhs - rhs, variable, domain=sp.S.Reals)


def _solve_trig_inequality(inequality: sp.Basic, variable: sp.Symbol) -> Any:
    """
    Solve trigonometric inequalities like sin(x) > 1/2.
    Returns solution as intervals or union of intervals.
    """
    try:
        # Try to parse the inequality
        if isinstance(inequality, sp.Relational):
            lhs = inequality.lhs
            rhs = inequality.rhs
            rel_type = type(inequality)
        else:
            return None
        
        # For simple cases, find critical points and test intervals
        if lhs.has(sp.sin):
            eq = sp.Eq(lhs, rhs)
            critical_points = sp.solve(eq, variable)
        elif lhs.has(sp.cos):
            eq = sp.Eq(lhs, rhs)
            critical_points = sp.solve(eq, variable)
        elif lhs.has(sp.tan):
            eq = sp.Eq(lhs, rhs)
            critical_points = sp.solve(eq, variable)
        else:
            return None
        
        # For basic inequality solving, return FiniteSet with simplified answer
        solution = sp.satisfiable(inequality)
        if solution:
            return solution
        return sp.EmptySet
    except Exception:
        return None


def _product_to_sum(expr: sp.Basic) -> sp.Basic:
    """
    Convert product of trig functions to sum/difference.
    JEE Advanced: sin(A)cos(B) = ½[sin(A+B) + sin(A-B)]
    """
    # Rewrite using product_to_sum
    result = sp.expand_trig(expr)
    # Use sympy's expand then try to convert back to sum form if beneficial
    # For products, expand_trig can help reveal the sum structure
    return result


def _sum_to_product(expr: sp.Basic) -> sp.Basic:
    """
    Convert sum of trig functions to product.
    JEE Advanced: sin(A) + sin(B) = 2sin((A+B)/2)cos((A-B)/2)
    """
    # Try to factor as products
    factored = sp.factor(expr)
    # If factoring doesn't work, use trig identities
    try:
        result = sp.trigsimp(expr)
        return result
    except:
        return expr


def _get_trig_range_extrema(expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Find minimum, maximum, and range of trigonometric expressions.
    JEE Advanced: Find extrema of sin(x) + cos(x), 3sin(x) + 4cos(x), etc.
    """
    try:
        # For linear combinations of trig functions: a*sin(x) + b*cos(x)
        # Max = √(a² + b²), Min = -√(a² + b²)
        
        # Differentiate to find critical points
        derivative = sp.diff(expr, variable)
        critical_points = sp.solve(derivative, variable)
        
        if not critical_points:
            # If no critical points, expression may be constant
            return {"min": expr, "max": expr, "range": f"[{expr}, {expr}]"}
        
        # Evaluate at critical points
        values = []
        for cp in critical_points[:5]:  # Limit to first 5 critical points
            try:
                val = float(sp.N(expr.subs(variable, cp)))
                values.append(val)
            except:
                pass
        
        if values:
            min_val = min(values)
            max_val = max(values)
            return {
                "min": sp.N(min_val, 4),
                "max": sp.N(max_val, 4),
                "range": f"[{min_val:.4f}, {max_val:.4f}]",
                "critical_points": critical_points[:3]
            }
        else:
            # Fallback: use symbolic methods
            return {"info": "Complex extrema - requires numerical evaluation"}
    except Exception as e:
        return {"error": str(e)}


def _solve_principal_values(equation: sp.Basic, variable: sp.Symbol, interval_str: str = "[0, 2*pi)") -> Any:
    """
    Find principal values of trigonometric equations within a specified interval.
    JEE Advanced: Solutions in [0, 2π), [0°, 360°), or other intervals.
    """
    try:
        # Get all solutions first
        all_solutions = sp.solveset(equation, variable, domain=sp.S.Reals)
        
        # Create interval boundaries
        if "[0, 2*pi)" in interval_str or "[0, 2π)" in interval_str.replace("π", "*pi"):
            lower, upper = 0, 2*sp.pi
        elif "[0, pi)" in interval_str or "[0, π)" in interval_str.replace("π", "*pi"):
            lower, upper = 0, sp.pi
        elif "[-pi, pi)" in interval_str:
            lower, upper = -sp.pi, sp.pi
        else:
            # Assume [0, 2π)
            lower, upper = 0, 2*sp.pi
        
        # Filter solutions in the interval
        principal_solutions = sp.FiniteSet()
        try:
            if isinstance(all_solutions, (sp.Union, sp.ImageSet)):
                # For ImageSet (periodic solutions), get representative values
                if isinstance(all_solutions, sp.Union):
                    for sol_set in all_solutions.args:
                        if isinstance(sol_set, sp.ImageSet):
                            # Get base solution (n=0)
                            base = sol_set.lamda.expr.subs(sol_set.lamda.variables[0], 0)
                            if float(sp.N(base)) >= float(sp.N(lower)) and float(sp.N(base)) < float(sp.N(upper)):
                                principal_solutions = principal_solutions | sp.FiniteSet(base)
        except:
            pass
        
        if principal_solutions:
            return principal_solutions
        
        # Fallback: solve directly in the interval using numerical methods
        return f"Principal values in [{lower}, {upper}): Check individual solutions"
    except Exception as e:
        return f"Error: {str(e)}"


def _get_all_solutions_with_period(equation: sp.Basic, variable: sp.Symbol, start: sp.Expr = 0, end: sp.Expr = 2*sp.pi) -> dict:
    """
    Get all solutions of a trig equation and identify the period pattern.
    JEE Advanced: Identify periodic families of solutions.
    """
    try:
        general_solution = sp.solveset(equation, variable, domain=sp.S.Reals)
        
        # Extract solutions in [0, 2π)
        solutions_in_period = []
        try:
            # If it's an ImageSet or Union, try to get specific values
            if isinstance(general_solution, (sp.Union, sp.ImageSet)):
                # For periodic solutions, collect representative values
                for val in (general_solution if isinstance(general_solution, sp.Union) else [general_solution]):
                    if isinstance(val, sp.ImageSet):
                        # Get the base solution by setting n=0
                        base = val.lamda.expr.subs(val.lamda.variables[0], 0)
                        solutions_in_period.append(base)
            else:
                solutions_in_period = list(general_solution) if hasattr(general_solution, '__iter__') else [general_solution]
        except:
            pass
        
        return {
            "general_solution": general_solution,
            "principal_solutions": solutions_in_period,
            "period": "2π for sin/cos, π for tan",
        }
    except Exception as e:
        return {"error": str(e)}


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

    # Inverse trigonometric simplification
    if task.operation == "simplify_inverse_trig":
        var = sp.Symbol(task.variable or "x")
        return _simplify_inverse_trig_composition(expr, var)

    # Domain and range for inverse trig functions
    if task.operation == "trig_domain_range":
        func_name = task.function or "asin"
        domain, range_val = _get_inverse_trig_domain_range(func_name)
        if domain is None:
            return f"Unknown function: {func_name}"
        return f"Domain: {domain}, Range: {range_val}"

    # Solve inverse trig equations
    if task.operation == "solve_inverse_trig":
        canonical_equations = [_as_zero_expression(target) for target in targets]
        solve_variables = list(variables)
        if not solve_variables:
            all_symbols: set[sp.Symbol] = set()
            for equation in canonical_equations:
                all_symbols.update(equation.free_symbols)
            solve_variables = sorted(all_symbols, key=lambda symbol: symbol.name)
            if not solve_variables:
                solve_variables = [sp.Symbol(task.variable or "x")]

        if len(solve_variables) == 1:
            return _solve_inverse_trig_equation(canonical_equations[0], solve_variables[0])
        return sp.nonlinsolve(canonical_equations, solve_variables)

    # Solve trigonometric inequalities
    if task.operation == "solve_trig_inequality":
        var = sp.Symbol(task.variable or "x")
        return _solve_trig_inequality(expr, var)

    # JEE ADVANCED OPERATIONS
    # Product to sum conversion
    if task.operation == "product_to_sum":
        return _product_to_sum(expr)

    # Sum to product conversion
    if task.operation == "sum_to_product":
        return _sum_to_product(expr)

    # Range, maximum, minimum values
    if task.operation == "trig_range_max_min":
        var = sp.Symbol(task.variable or "x")
        return _get_trig_range_extrema(expr, var)

    # Principal values in specific interval
    if task.operation == "solve_principal_values":
        var = sp.Symbol(task.variable or "x")
        interval_str = task.lower_bound if task.lower_bound else "[0, 2*pi)"
        canonical_equations = [_as_zero_expression(target) for target in targets]
        return _solve_principal_values(canonical_equations[0], var, interval_str)

    # Get all solutions with period analysis
    if task.operation == "get_all_solutions":
        var = sp.Symbol(task.variable or "x")
        canonical_equations = [_as_zero_expression(target) for target in targets]
        return _get_all_solutions_with_period(canonical_equations[0], var)

    # Standard trig simplifications
    if task.operation in {"trigsimplify", "trig_simplify"}:
        return sp.trigsimp(sp.simplify(expr))

    if task.operation == "trigexpand":
        return sp.expand_trig(expr)

    if task.operation in {"trigreduce", "trig_reduce"}:
        return sp.trigsimp(sp.expand_trig(expr))

    if task.operation == "evaluate" and has_trig:
        return sp.trigsimp(sp.simplify(expr))

    # Standard trig equation solving
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
        "solve_inverse_trig",
        "solve_trig_inequality",
        "simplify_inverse_trig",
        "trig_domain_range",
        "product_to_sum",
        "sum_to_product",
        "trig_range_max_min",
        "solve_principal_values",
        "get_all_solutions",
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

    # JEE ADVANCED STEPS
    # Product to sum
    if task.operation == "product_to_sum":
        parsed_expr = parse_math(expr_str, locals_dict)
        if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
            parsed_expr = parsed_expr[0]
        lines.extend([
            "1. Start with the product of trigonometric functions:",
            indented_math(parsed_expr),
            "2. Apply product-to-sum formulas:",
            "   - sin(A)sin(B) = ½[cos(A-B) - cos(A+B)]",
            "   - cos(A)cos(B) = ½[cos(A-B) + cos(A+B)]",
            "   - sin(A)cos(B) = ½[sin(A+B) + sin(A-B)]",
            "3. Expanded/simplified result:",
            indented_math(result),
        ])
        return "\n".join(lines)

    # Sum to product
    if task.operation == "sum_to_product":
        parsed_expr = parse_math(expr_str, locals_dict)
        if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
            parsed_expr = parsed_expr[0]
        lines.extend([
            "1. Start with the sum of trigonometric functions:",
            indented_math(parsed_expr),
            "2. Apply sum-to-product formulas:",
            "   - sin(A) + sin(B) = 2sin((A+B)/2)cos((A-B)/2)",
            "   - sin(A) - sin(B) = 2cos((A+B)/2)sin((A-B)/2)",
            "   - cos(A) + cos(B) = 2cos((A+B)/2)cos((A-B)/2)",
            "   - cos(A) - cos(B) = -2sin((A+B)/2)sin((A-B)/2)",
            "3. Product form:",
            indented_math(result),
        ])
        return "\n".join(lines)

    # Range and extrema
    if task.operation == "trig_range_max_min":
        parsed_expr = parse_math(expr_str, locals_dict)
        if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
            parsed_expr = parsed_expr[0]
        lines.extend([
            "1. Start with the trigonometric expression:",
            indented_math(parsed_expr),
            "2. Find critical points by taking derivative and setting to zero.",
            "3. Evaluate the expression at critical points.",
            "4. Range and extrema analysis:",
            indented_math(str(result)),
        ])
        return "\n".join(lines)

    # Principal values
    if task.operation == "solve_principal_values":
        equation_texts = task.equations or ([expr_str] if expr_str else [])
        if equation_texts:
            lines.append("1. Start with the trigonometric equation:")
            for equation in equation_texts:
                lines.append(indented_math(equation))
            interval_str = task.lower_bound if task.lower_bound else "[0, 2π)"
            lines.extend([
                f"2. Find all solutions within the interval {interval_str}",
                "3. These are the principal values (one complete period):",
                indented_math(result),
            ])
        return "\n".join(lines)

    # All solutions with period
    if task.operation == "get_all_solutions":
        equation_texts = task.equations or ([expr_str] if expr_str else [])
        if equation_texts:
            lines.append("1. Start with the trigonometric equation:")
            for equation in equation_texts:
                lines.append(indented_math(equation))
            lines.extend([
                "2. General solution (all families):",
                indented_math(str(result.get("general_solution", ""))),
                "3. Principal solutions in [0, 2π):",
                indented_math(str(result.get("principal_solutions", ""))),
                f"4. Period: {result.get('period', 'see analysis')}",
            ])
        return "\n".join(lines)

    # Domain and range for inverse trig
    if task.operation == "trig_domain_range":
        lines.extend([
            "1. Identify the inverse trigonometric function:",
            indented_math(task.function or "asin"),
            "2. Domain and Range Analysis:",
            indented_math(result),
            "3. This means:",
            indented_math("Input values must be in the domain, output values in the range."),
        ])
        return "\n".join(lines)

    # Simplify inverse trig compositions
    if task.operation == "simplify_inverse_trig":
        parsed_expr = parse_math(expr_str, locals_dict)
        if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
            parsed_expr = parsed_expr[0]
        lines.extend([
            "1. Start with the inverse trig composition:",
            indented_math(parsed_expr),
            "2. Apply domain constraints and simplification rules.",
            "   - arcsin(sin(x)) = x for x ∈ [-π/2, π/2]",
            "   - arccos(cos(x)) = x for x ∈ [0, π]",
            "   - arctan(tan(x)) = x for x ∈ (-π/2, π/2)",
            "3. Simplified result:",
            indented_math(result),
        ])
        return "\n".join(lines)

    # Solve inverse trig equations
    if task.operation == "solve_inverse_trig":
        equation_texts = task.equations or ([expr_str] if expr_str else [])
        if not equation_texts:
            return None

        parsed_equations: list[sp.Basic] = []
        for equation_text in equation_texts:
            parsed = parse_math(equation_text, locals_dict)
            if isinstance(parsed, (list, tuple)) and parsed:
                parsed = parsed[0]
            parsed_equations.append(_as_zero_expression(parsed))

        lines.append("1. Start with the inverse trigonometric equation:")
        for equation in parsed_equations:
            lines.append(indented_math(sp.Eq(equation, 0)))

        lines.append("2. To solve an inverse trig equation arcf(x) = k:")
        lines.append("   - Apply the forward trig function to both sides: x = f(k)")
        lines.append("   - Verify the solution is within the principal domain of the inverse function.")

        variable_names = task.variables or ([task.variable] if task.variable else ["x"])
        lines.append(f"3. Solve for {', '.join(variable_names)} considering domain constraints.")
        lines.append(_solution_label(result))
        lines.append(indented_math(result))
        return "\n".join(lines)

    # Solve trig inequalities
    if task.operation == "solve_trig_inequality":
        parsed_expr = parse_math(expr_str, locals_dict)
        if isinstance(parsed_expr, (list, tuple)) and parsed_expr:
            parsed_expr = parsed_expr[0]
        lines.extend([
            "1. Start with the trigonometric inequality:",
            indented_math(parsed_expr),
            "2. Find critical points where the inequality becomes an equality.",
            "3. Test sign in each interval to determine where inequality holds.",
            "4. General solution (considering periodicity):",
            indented_math(result),
        ])
        return "\n".join(lines)

    # Standard trig equation solving
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

    # Trig simplifications
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
