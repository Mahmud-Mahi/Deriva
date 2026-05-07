import sympy as sp
from typing import Any
from models import MathTask
from formatter import indented_math, pretty_math, parse_math

SYMPY_LOCALS = {
    "Function": sp.Function, 
    "Derivative": sp.Derivative, 
    "dsolve": sp.dsolve,
    "idiff": sp.idiff
}

RULES = [
    "For DIFFERENTIAL EQUATIONS: Use operation 'solve_ode'. Represent y as a function of x: Function('y')(x).",
    "For INTEGRALS: Set 'lower_bound' and 'upper_bound' if definite.",
    "For IMPLICIT DIFFERENTIATION or INFINITE NESTED RADICALS (...∞): Use operation 'differentiate'. Rewrite infinite roots algebraically (e.g. y = sqrt(x + y) -> Eq(y**2, x + y)).",
    "For INVERSE TRIG FUNCTIONS: Use asin, acos, atan, acot. Do NOT use ^-1. Do NOT wrap standard expressions in brackets [...] as they create lists.",
    "For TRIGONOMETRIC EXPANSION (sin(A+B), cos(A-B), tan(A+B), etc.): Use operation 'trigexpand'. This expands to component terms like sin(A)cos(B) + cos(A)sin(B).",
    "IMPORTANT: If user types sin(A+B) or similar trig expression without equals sign, use 'trigexpand' operation to get the expanded form."
]

EXAMPLES = [
    'User problem: Solve dy/dx = x * y\nJSON: {"operation":"solve_ode","equation":"Eq(Derivative(Function(\'y\')(x), x), x * Function(\'y\')(x))","variable":"x"}',
    'User problem: differentiate y = sqrt(tan(x) + sqrt(tan(x) + ...))\nJSON: {"operation":"differentiate","equation":"Eq(y**2, tan(x) + y)","variables":["y", "x"]}',
    'User problem: differentiate tan^-1(cot(x))\nJSON: {"operation":"differentiate","expression":"atan(cot(x))","variable":"x"}',
    'User problem: expand sin(a+b)\nJSON: {"operation":"trigexpand","expression":"sin(a + b)"}',
    'User problem: expand cos(a-b)\nJSON: {"operation":"trigexpand","expression":"cos(a - b)"}',
    'User problem: expand sin(A+B)\nJSON: {"operation":"trigexpand","expression":"sin(A + B)"}',
    'User problem: expand cos(A-B)\nJSON: {"operation":"trigexpand","expression":"cos(A - B)"}',
    'User problem: expand tan(A+B)\nJSON: {"operation":"trigexpand","expression":"tan(A + B)"}'
]

# We define y_sym locally to ensure we have a SYMBOL for differentiation
y_sym = sp.Symbol('y')
x_sym = sp.Symbol('x')

# --- HELPER FUNCTIONS FOR SPECIALIZED INTEGRATION ---

def circle_root_radius(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic | None:
    if isinstance(expr, list): return None
    if not expr.is_Pow or expr.exp != sp.Rational(1, 2): return None
    inside = sp.expand(expr.base)
    coeff = inside.coeff(variable, 2)
    constant = inside.subs(variable, 0)
    remainder = sp.simplify(inside - constant - coeff * variable**2)
    if coeff == -1 and remainder == 0 and constant.is_positive:
        return sp.sqrt(constant)
    return None

def degree_one_poly(expr: sp.Basic, variable: sp.Symbol) -> sp.Poly | None:
    try: poly = sp.Poly(expr, variable, domain="EX")
    except (sp.PolynomialError, TypeError): return None
    return poly if poly.degree() == 1 else None

def linear_root_log_antiderivative(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic | None:
    if isinstance(expr, list): return None
    numerator, denominator = sp.fraction(sp.factor(expr))
    if numerator != 1: return None

    factors = denominator.args if denominator.is_Mul else (denominator,)
    root_factor = None
    linear_poly = None

    for factor in factors:
        if factor.is_Pow and factor.exp == sp.Rational(1, 2):
            root_factor = factor
            continue
        poly = degree_one_poly(factor, variable)
        if poly is not None: linear_poly = poly

    if root_factor is None or linear_poly is None: return None
    root_poly = degree_one_poly(root_factor.base, variable)
    if root_poly is None: return None

    a = linear_poly.coeff_monomial(variable)
    b = linear_poly.coeff_monomial(1)
    c = root_poly.coeff_monomial(variable)
    d = root_poly.coeff_monomial(1)
    k = sp.simplify((b * c - a * d) / a)

    if k.is_negative is not True: return None
    m = sp.sqrt(-k)
    root = sp.sqrt(c * variable + d)
    return sp.simplify(sp.log(sp.Abs((root - m) / (root + m))) / (a * m))

def trig_power_antiderivative(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic | None:
    if isinstance(expr, list) or not expr.is_Pow or expr.exp != 4: return None
    base = expr.base
    if base == sp.sin(variable):
        return sp.Rational(3, 8) * variable - sp.sin(2 * variable) / 4 + sp.sin(4 * variable) / 32
    if base == sp.cos(variable):
        return sp.Rational(3, 8) * variable + sp.sin(2 * variable) / 4 + sp.sin(4 * variable) / 32
    return None

def antiderivative_method_steps(expr: sp.Basic, variable: sp.Symbol) -> list[str]:
    if isinstance(expr, list): return ["2. Method: Apply standard integration rules."]
    
    trig_antiderivative = trig_power_antiderivative(expr, variable)
    if trig_antiderivative is not None:
        return [
            "2. Method to find the antiderivative:",
            "   Since the trig power is even, use the power-reduction identity.",
            "   Apply sin²(x) = (1 - cos(2x))/2 or cos²(x) = (1 + cos(2x))/2.",
            "   This reduces the integrand to a first-degree trigonometric expression."
        ]

    log_antiderivative = linear_root_log_antiderivative(expr, variable)
    if log_antiderivative is not None:
        return [
            "2. Method to find the antiderivative:",
            "   This integral has the form 1 / ( (ax+b) * sqrt(cx+d) ).",
            "   Use the substitution t = sqrt(cx + d) to rationalize the integrand.",
            "   After substitution, use partial fraction decomposition or the standard log form result."
        ]

    radius = circle_root_radius(expr, variable)
    if radius is not None:
        theta = sp.Symbol("theta")
        substitution = sp.Eq(variable, radius * sp.sin(theta), evaluate=False)
        return [
            "2. Method to find the antiderivative:",
            f"   The integrand matches the form sqrt(a² - x²), suggesting trigonometric substitution.",
            "   Let:", indented_math(substitution),
            "   Use the identity cos²(θ) = 1 - sin²(θ) to remove the square root.",
            "   Then integrate with respect to θ and substitute back to x."
        ]

    # Integration by Parts Detection
    if expr.is_Mul:
        args = expr.args
        if any(isinstance(a, (sp.exp, sp.sin, sp.cos, sp.log)) for a in args):
            return ["2. Method: Integration by Parts (∫u dv = uv - ∫v du) is recommended here."]

    return ["2. Method: Apply standard integration rules and simplify the result."]

# --- EXECUTION LOGIC ---

def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    # Fix for LLM wrapping in list due to user brackets [...]
    if isinstance(expr, list):
        if not expr: return None
        expr = expr[0]

    if task.operation == "solve_ode": 
        return sp.dsolve(expr)
    
    if task.operation == "differentiate": 
        # 1. Determine the variable to differentiate with respect to
        # If user provided variables, use the last one (usually 'x' in [y, x])
        if variables:
            indep_var = variables[-1]
        else:
            # Try to find a symbol in the expression, fallback to x_sym
            symbols = list(expr.free_symbols)
            indep_var = symbols[0] if symbols else x_sym

        # 2. Handle Equations (Implicit or Explicit Equality)
        if getattr(expr, "is_Equality", False):
            # If it's a simple 'y = ...' where y is a symbol or function
            lhs_is_y = (expr.lhs == y_sym or (hasattr(expr.lhs, 'func') and expr.lhs.func.__name__ == 'y'))
            
            if lhs_is_y and y_sym not in expr.rhs.free_symbols:
                return sp.simplify(sp.trigsimp(sp.diff(expr.rhs, indep_var)))
            
            # True Implicit Differentiation (e.g., x^2 + y^2 = 1)
            implicit_expr = expr.lhs - expr.rhs
            # We need y as a symbol for idiff
            try:
                # Search for any symbol named 'y' or the Function 'y'
                target_y = None
                for s in implicit_expr.free_symbols:
                    if s.name == 'y':
                        target_y = s
                        break
                
                if target_y:
                    raw_diff = sp.idiff(implicit_expr, target_y, indep_var)
                else:
                    raw_diff = sp.diff(implicit_expr, indep_var)
                return sp.simplify(sp.trigsimp(raw_diff))
            except:
                return sp.simplify(sp.trigsimp(sp.diff(implicit_expr, indep_var)))

        # 3. Standard Explicit Differentiation (The path for your tan^-1 problem)
        return sp.simplify(sp.trigsimp(sp.diff(expr, indep_var)))

    if task.operation == "limit": 
        if not task.point: raise ValueError("Limit operation requires a 'point'.")
        from modules import get_all_locals
        point = parse_math(task.point, get_all_locals())
        return sp.limit(expr, variables[0] if variables else sp.Symbol('x'), point, dir=task.direction)
        
    if task.operation == "integrate":
        variable = variables[0] if variables else sp.Symbol("x")
        if task.lower_bound and task.upper_bound:
            from modules import get_all_locals
            low = parse_math(task.lower_bound, get_all_locals())
            up = parse_math(task.upper_bound, get_all_locals())
            return sp.integrate(expr, (variable, low, up))

        # Prioritize custom antiderivatives for cleaner output
        custom_trig = trig_power_antiderivative(expr, variable)
        if custom_trig is not None: return custom_trig
        custom_log = linear_root_log_antiderivative(expr, variable)
        if custom_log is not None: return custom_log

        return sp.simplify(sp.integrate(expr, variable))

    if task.operation == "trigexpand":
        return sp.expand_trig(expr)

    return None

# --- STEP GENERATION ---

def get_steps(task: MathTask, expr_str: str, result: Any):
    from modules import get_all_locals
    locals_dict = get_all_locals()
    lines = []
    
    if task.operation == "solve_ode":
        lines.extend([
            "1. Identify the Differential Equation:", indented_math(expr_str), 
            "2. Determine equation type (separable, linear, exact, etc.).", 
            "3. Result:", indented_math(result)
        ])
        return "\n".join(lines)
        
    if task.operation == "differentiate":
        lines.extend([
            "1. Start with the function/expression:", indented_math(expr_str), 
            "2. Apply differentiation rules (Chain rule, Product rule, or Implicit differentiation).", 
            "3. The derivative is:", indented_math(result)
        ])
        return "\n".join(lines)
        
    if task.operation == "integrate":
        expr = parse_math(expr_str, locals_dict)
        if isinstance(expr, list) and len(expr) > 0: expr = expr[0]
        variable = sp.Symbol(task.variable) if task.variable else sp.Symbol('x')

        lines.append("1. Identify the integrand:")
        lines.append(indented_math(expr))
        lines.extend(antiderivative_method_steps(expr, variable))
        lines.append("3. Final result:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    if task.operation == "trigexpand":
        lines.extend([
            "1. Start with the trigonometric expression:", indented_math(expr_str),
            "2. Apply trigonometric addition/subtraction identities:",
            "   • sin(A±B) = sin(A)cos(B) ± cos(A)sin(B)",
            "   • cos(A±B) = cos(A)cos(B) ∓ sin(A)sin(B)",
            "   • tan(A±B) = (tan(A) ± tan(B)) / (1 ∓ tan(A)tan(B))",
            "3. The expanded form is:",
            indented_math(result),
            "4. Final Identity:",
            indented_math(sp.Eq(sp.sin(sp.Symbol('A') + sp.Symbol('B')), result))
        ])
        return "\n".join(lines)

    return None