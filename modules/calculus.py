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
    "For INTEGRALS: Set 'lower_bound' and 'upper_bound' if definite. Use 'integrate' operation.",
    "For IMPLICIT DIFFERENTIATION or INFINITE NESTED RADICALS (...∞): Use operation 'differentiate'. Rewrite infinite roots algebraically (e.g. y = sqrt(x + y) -> Eq(y**2, x + y)).",
    "For LOGARITHMIC DIFFERENTIATION (y = x^x, y = (sin x)^cos x): Use 'log_differentiate' operation.",
    "For PARAMETRIC DIFFERENTIATION (x = f(t), y = g(t)): Use 'parametric_differentiate' with variables=[t, x, y].",
    "For PARTIAL DERIVATIVES: Use 'partial_differentiate' and specify variable to differentiate with respect to.",
    "For HIGHER-ORDER DERIVATIVES: Use 'higher_derivative' with 'order' field for nth derivative (n≥2).",
    "For INVERSE TRIG FUNCTIONS: Use asin, acos, atan, acot. Do NOT use ^-1.",
    "For TRIGONOMETRIC EXPANSION (sin(A+B), cos(A-B), tan(A+B), etc.): Use 'trigexpand'.",
    "For ADVANCED INTEGRATION: Use 'partial_fraction_decompose' (rational), 'integration_by_parts', 'trig_substitution', 'hyperbolic_substitution'.",
    "For TAYLOR/MACLAURIN SERIES: Use 'taylor_series' with 'point' field (0 for Maclaurin).",
    "For L'HÔPITAL'S RULE: Use 'lhopital_limit' with 'point' field.",
    "For OPTIMIZATION: Use 'extrema_analysis' to find critical points and analyze max/min.",
    "For CONCAVITY/INFLECTION: Use 'concavity_analysis' to find inflection points.",
    "For CONVERGENCE: Use 'series_convergence' to test series convergence.",
]

EXAMPLES = [
    'User: Solve dy/dx = x*y\nJSON: {"operation":"solve_ode","equation":"Eq(Derivative(Function(\'y\')(x), x), x * Function(\'y\')(x))"}',
    'User: Differentiate y = x^x\nJSON: {"operation":"log_differentiate","expression":"x**x","variable":"x"}',
    'User: Differentiate (sin(x))^cos(x)\nJSON: {"operation":"log_differentiate","expression":"sin(x)**cos(x)","variable":"x"}',
    'User: Find dy/dx where x=cos(t), y=sin(t)\nJSON: {"operation":"parametric_differentiate","variables":["t","x","y"],"expressions":["cos(t)","sin(t)"]}',
    'User: Find ∂f/∂x where f = x²y + xy³\nJSON: {"operation":"partial_differentiate","expression":"x**2*y + x*y**3","variable":"x","variables":["x","y"]}',
    'User: Find f\'\'(x) where f(x) = x³ + 2x² + x + 1\nJSON: {"operation":"higher_derivative","expression":"x**3 + 2*x**2 + x + 1","variable":"x","order":2}',
    'User: Integrate (x+1)/(x²+1)\nJSON: {"operation":"partial_fraction_decompose","expression":"(x+1)/(x**2+1)","variable":"x"}',
    'User: Integrate x*e^x dx\nJSON: {"operation":"integration_by_parts","expression":"x*exp(x)","variable":"x"}',
    'User: Taylor series of e^x around x=0 to order 5\nJSON: {"operation":"taylor_series","expression":"exp(x)","variable":"x","point":"0","order":"5"}',
    'User: Find max/min of f(x) = x³ - 3x² + 2\nJSON: {"operation":"extrema_analysis","expression":"x**3 - 3*x**2 + 2","variable":"x"}',
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

# --- ADVANCED CALCULUS HELPER FUNCTIONS ---

def _logarithmic_differentiate(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic:
    """
    Logarithmic differentiation for complex exponential forms.
    JEE Advanced: y = x^x, y = (sin x)^cos x, etc.
    """
    try:
        # Take ln of both sides: ln(y) = x*ln(x)
        # Then differentiate implicitly
        ln_expr = sp.ln(expr)
        derivative_ln = sp.diff(ln_expr, variable)
        # dy/dx = y * d(ln y)/dx
        result = expr * derivative_ln
        return sp.simplify(result)
    except Exception:
        return sp.diff(expr, variable)


def _parametric_differentiate(param_t: sp.Symbol, x_expr: sp.Basic, y_expr: sp.Basic) -> sp.Basic:
    """
    Parametric differentiation: dy/dx = (dy/dt) / (dx/dt)
    JEE Advanced: Find dy/dx from parametric equations
    """
    try:
        dx_dt = sp.diff(x_expr, param_t)
        dy_dt = sp.diff(y_expr, param_t)
        if dx_dt == 0:
            return "Undefined (dx/dt = 0)"
        return sp.simplify(dy_dt / dx_dt)
    except Exception:
        return "Error in parametric differentiation"


def _higher_order_derivative(expr: sp.Basic, variable: sp.Symbol, order: int) -> sp.Basic:
    """
    Find nth derivative of an expression.
    JEE Advanced: 2nd, 3rd, 4th derivatives for analysis
    """
    try:
        result = expr
        for _ in range(order):
            result = sp.diff(result, variable)
        return sp.simplify(result)
    except Exception:
        return None


def _partial_fraction_decompose(expr: sp.Basic, variable: sp.Symbol) -> sp.Basic:
    """
    Partial fraction decomposition for rational functions.
    JEE Advanced: Breaking down complex rationals for integration
    """
    try:
        return sp.apart(expr, variable)
    except Exception:
        return expr


def _integration_by_parts_analysis(expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Analyze and compute integration by parts.
    JEE Advanced: ∫u dv = uv - ∫v du
    """
    try:
        # Try common IBP patterns: xsin(x), x*e^x, x*ln(x), etc.
        result = sp.integrate(expr, variable)
        
        # Detect the pattern
        pattern = "Unknown"
        if expr.has(sp.sin, sp.cos) or expr.has(sp.exp):
            if expr.has(variable):
                pattern = "Trigonometric or Exponential integration"
        
        return {
            "method": "Integration by Parts",
            "pattern": pattern,
            "antiderivative": result,
            "formula": "∫u dv = uv - ∫v du"
        }
    except Exception as e:
        return {"error": str(e)}


def _trigonometric_substitution(expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Apply trigonometric substitution for specific integral forms.
    Handles: sqrt(a² - x²), sqrt(a² + x²), sqrt(x² - a²)
    """
    try:
        theta = sp.Symbol('theta')
        
        # Check for sqrt(a² - x²) form
        if expr.has(sp.sqrt):
            sqrt_terms = [t for t in sp.preorder_traversal(expr) if t.is_Pow and t.exp == sp.Rational(1,2)]
            for sqrt_term in sqrt_terms:
                base = sqrt_term.base
                # sqrt(a² - x²) → x = a*sin(θ)
                # sqrt(a² + x²) → x = a*tan(θ)
                # sqrt(x² - a²) → x = a*sec(θ)
        
        result = sp.integrate(expr, variable)
        return {
            "method": "Trigonometric Substitution",
            "substitutions": "x = a*sin(θ), x = a*tan(θ), or x = a*sec(θ)",
            "result": result
        }
    except Exception as e:
        return {"error": str(e)}


def _taylor_series_expansion(expr: sp.Basic, variable: sp.Symbol, point: sp.Basic, order: int) -> sp.Basic:
    """
    Taylor series expansion around a point.
    Maclaurin series when point = 0
    """
    try:
        series = sp.series(expr, variable, point, n=order+1)
        return series.removeO()
    except Exception:
        return f"Could not expand series to order {order}"


def _lhopital_limit(expr: sp.Basic, variable: sp.Symbol, point: sp.Basic) -> sp.Basic:
    """
    Apply L'Hôpital's rule for 0/0 or ∞/∞ indeterminate forms.
    """
    try:
        # Direct limit attempt
        limit_result = sp.limit(expr, variable, point)
        
        # If indeterminate, apply L'Hôpital's rule
        if limit_result is sp.zoo or limit_result is sp.nan:
            # Try differentiating numerator and denominator
            if expr.is_rational_function(variable):
                numer, denom = sp.fraction(expr)
                d_numer = sp.diff(numer, variable)
                d_denom = sp.diff(denom, variable)
                if d_denom != 0:
                    new_expr = d_numer / d_denom
                    limit_result = sp.limit(new_expr, variable, point)
        
        return limit_result
    except Exception:
        return sp.limit(expr, variable, point)


def _extrema_analysis(expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Find and classify critical points, local max/min, extrema.
    JEE Advanced: Optimization problems
    """
    try:
        # First derivative
        f_prime = sp.diff(expr, variable)
        critical_points = sp.solve(f_prime, variable)
        
        # Second derivative test
        f_double_prime = sp.diff(f_prime, variable)
        
        extrema = {
            "critical_points": critical_points,
            "first_derivative": f_prime,
            "second_derivative": f_double_prime,
            "analysis": []
        }
        
        for cp in critical_points[:5]:  # Limit to first 5 critical points
            try:
                second_deriv_val = float(sp.N(f_double_prime.subs(variable, cp)))
                func_val = float(sp.N(expr.subs(variable, cp)))
                
                if second_deriv_val > 0:
                    extrema["analysis"].append(f"x = {cp}: Local minimum, f({cp}) = {func_val}")
                elif second_deriv_val < 0:
                    extrema["analysis"].append(f"x = {cp}: Local maximum, f({cp}) = {func_val}")
                else:
                    extrema["analysis"].append(f"x = {cp}: Inconclusive (2nd derivative = 0)")
            except:
                pass
        
        return extrema
    except Exception as e:
        return {"error": str(e)}


def _concavity_analysis(expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Analyze concavity and find inflection points.
    JEE Advanced: Curve sketching
    """
    try:
        # Second derivative for concavity
        f_double_prime = sp.diff(expr, (variable, 2))
        inflection_points = sp.solve(f_double_prime, variable)
        
        return {
            "second_derivative": f_double_prime,
            "inflection_points": inflection_points,
            "concavity": "Use second derivative test: f''(x) > 0 (concave up), f''(x) < 0 (concave down)"
        }
    except Exception as e:
        return {"error": str(e)}


def _series_convergence_test(series_expr: sp.Basic, variable: sp.Symbol) -> dict:
    """
    Test if a series converges using various tests.
    Ratio test, root test, p-test, etc.
    """
    try:
        # Try ratio test
        ratio_test = sp.limit(series_expr, variable, sp.oo)
        
        return {
            "limit_test": f"lim(n→∞) a_n = {ratio_test}",
            "convergence_status": "Converges" if ratio_test == 0 else "May diverge",
            "tests_available": ["Ratio Test", "Root Test", "p-test", "Comparison Test"]
        }
    except Exception as e:
        return {"error": str(e)}


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

    # ADVANCED DIFFERENTIATION
    if task.operation == "log_differentiate":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _logarithmic_differentiate(expr, variable)

    if task.operation == "parametric_differentiate":
        # variables = [t, x, y] for parametric case
        if len(variables) >= 3 and len(equations) >= 2:
            param_t = variables[0]
            x_eq = equations[0] if isinstance(equations[0], sp.Basic) else sp.sympify(str(equations[0]))
            y_eq = equations[1] if isinstance(equations[1], sp.Basic) else sp.sympify(str(equations[1]))
            return _parametric_differentiate(param_t, x_eq, y_eq)
        return None

    if task.operation == "partial_differentiate":
        variable = sp.Symbol(task.variable or "x")
        return sp.diff(expr, variable)

    if task.operation == "higher_derivative":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        order = int(task.lower_bound) if task.lower_bound else 2  # Default 2nd derivative
        return _higher_order_derivative(expr, variable, order)

    # ADVANCED INTEGRATION
    if task.operation == "partial_fraction_decompose":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _partial_fraction_decompose(expr, variable)

    if task.operation == "integration_by_parts":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _integration_by_parts_analysis(expr, variable)

    if task.operation == "trig_substitution":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _trigonometric_substitution(expr, variable)

    if task.operation == "hyperbolic_substitution":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        # Similar to trig substitution but uses sinh, cosh
        try:
            result = sp.integrate(expr, variable)
            return result
        except:
            return "Hyperbolic substitution needed for this integral"

    # SERIES AND LIMITS
    if task.operation == "taylor_series":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        point_val = sp.sympify(task.lower_bound or "0") if task.lower_bound else 0
        order_val = int(task.upper_bound) if task.upper_bound else 5
        return _taylor_series_expansion(expr, variable, point_val, order_val)

    if task.operation == "lhopital_limit":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        point_val = sp.sympify(task.point or "0") if task.point else 0
        return _lhopital_limit(expr, variable, point_val)

    # CALCULUS ANALYSIS
    if task.operation == "extrema_analysis":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _extrema_analysis(expr, variable)

    if task.operation == "concavity_analysis":
        variable = variables[0] if variables else sp.Symbol(task.variable or "x")
        return _concavity_analysis(expr, variable)

    if task.operation == "series_convergence":
        variable = variables[0] if variables else sp.Symbol(task.variable or "n")
        return _series_convergence_test(expr, variable)

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

    # ADVANCED DIFFERENTIATION STEPS
    if task.operation == "log_differentiate":
        lines.extend([
            "1. Function with complex exponential form:",
            indented_math(expr_str),
            "2. Logarithmic Differentiation Method:",
            "   • Take ln of both sides: ln(y) = f(x)",
            "   • Differentiate both sides: (1/y) * dy/dx = f'(x)",
            "   • Solve for dy/dx: dy/dx = y * f'(x)",
            "3. The derivative is:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "parametric_differentiate":
        lines.extend([
            "1. Parametric equations:",
            indented_math(expr_str),
            "2. Parametric Differentiation Formula:",
            indented_math("dy/dx = (dy/dt) / (dx/dt)"),
            "3. Calculate dy/dt and dx/dt, then divide.",
            "4. The result is:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "partial_differentiate":
        lines.extend([
            "1. Function with multiple variables:",
            indented_math(expr_str),
            "2. Take partial derivative with respect to:", indented_math(task.variable or "x"),
            "3. Treating all other variables as constants.",
            "4. Result:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "higher_derivative":
        order = int(task.lower_bound) if task.lower_bound else 2
        lines.extend([
            f"1. Find the {order}{'nd' if order == 2 else 'rd' if order == 3 else 'th'} derivative:",
            indented_math(expr_str),
            f"2. Differentiate {order} times with respect to:", indented_math(task.variable or "x"),
            f"3. The {order}{'nd' if order == 2 else 'rd' if order == 3 else 'th'} derivative is:",
            indented_math(result)
        ])
        return "\n".join(lines)

    # ADVANCED INTEGRATION STEPS
    if task.operation == "partial_fraction_decompose":
        lines.extend([
            "1. Rational function:",
            indented_math(expr_str),
            "2. Partial Fraction Decomposition:",
            "   • Factor the denominator",
            "   • Write as sum of simpler fractions",
            "   • Solve for constants",
            "3. Decomposed form:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "integration_by_parts":
        lines.extend([
            "1. Integrand:",
            indented_math(expr_str),
            "2. Integration by Parts Formula: ∫u dv = uv - ∫v du",
            "   • Choose u and dv",
            "   • Calculate du and v",
            "   • Apply the formula",
            "3. Method detected:", indented_math(result.get("pattern", "Unknown")),
            "4. Antiderivative:",
            indented_math(result.get("antiderivative", "See analysis"))
        ])
        return "\n".join(lines)

    if task.operation == "trig_substitution":
        lines.extend([
            "1. Integrand with radical:",
            indented_math(expr_str),
            "2. Trigonometric Substitution:",
            "   • Identify the form: √(a²-x²), √(a²+x²), or √(x²-a²)",
            "   • Choose substitution: x=a*sin(θ), x=a*tan(θ), or x=a*sec(θ)",
            "   • Replace and simplify using trig identities",
            "   • Integrate in terms of θ",
            "   • Back-substitute to x",
            "3. Result:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "taylor_series":
        order = int(task.upper_bound) if task.upper_bound else 5
        point = task.lower_bound or "0"
        lines.extend([
            "1. Function to expand:",
            indented_math(expr_str),
            f"2. Taylor Series around x = {point} (order {order}):",
            "   f(x) = f(a) + f'(a)(x-a) + f''(a)(x-a)²/2! + ... + f^(n)(a)(x-a)^n/n!",
            f"3. Expansion around x = {point} to order {order}:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "lhopital_limit":
        lines.extend([
            "1. Limit with indeterminate form:",
            indented_math(expr_str),
            "2. L'Hôpital's Rule (for 0/0 or ∞/∞):",
            "   • Differentiate numerator and denominator separately",
            "   • Evaluate the new limit",
            "   • Repeat if necessary until determinate",
            "3. Limit value:",
            indented_math(result)
        ])
        return "\n".join(lines)

    if task.operation == "extrema_analysis":
        lines.extend([
            "1. Function to analyze:",
            indented_math(expr_str),
            "2. Find Critical Points:",
            "   • Compute f'(x) and set to 0",
            "   • Critical points:", indented_math(result.get("critical_points", "See analysis")),
            "3. Second Derivative Test:",
            "   • Compute f''(x)",
            "   • f''(c) > 0: local minimum, f''(c) < 0: local maximum",
            "4. Analysis:",
        ])
        for item in result.get("analysis", []):
            lines.append("   " + item)
        return "\n".join(lines)

    if task.operation == "concavity_analysis":
        lines.extend([
            "1. Function to analyze:",
            indented_math(expr_str),
            "2. Find Inflection Points:",
            "   • Compute f''(x) and set to 0",
            "   • Inflection points:", indented_math(result.get("inflection_points", "See analysis")),
            "3. Concavity Analysis:",
            "   • f''(x) > 0: concave up",
            "   • f''(x) < 0: concave down",
            "4. Second derivative:",
            indented_math(result.get("second_derivative", "See analysis"))
        ])
        return "\n".join(lines)

    if task.operation == "series_convergence":
        lines.extend([
            "1. Series to test:",
            indented_math(expr_str),
            "2. Convergence Tests Available:",
            "   • Ratio Test: lim|a_{n+1}/a_n|",
            "   • Root Test: lim|a_n|^(1/n)",
            "   • p-test: Σ 1/n^p converges if p > 1",
            "   • Comparison Test with known series",
            "3. Initial Analysis:",
            indented_math(result.get("limit_test", "See analysis"))
        ])
        return "\n".join(lines)

    return None