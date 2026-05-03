from . import algebra, calculus, matrix, geometry, combination
import sympy as sp

MODULES = [algebra, calculus, matrix, geometry, combination]

# Base SymPy Dictionary (Shared)
BASE_LOCALS = {
    "Symbol": sp.Symbol,
    "Integer": sp.Integer,
    "Float": sp.Float,
    "Rational": sp.Rational,
    "Eq": sp.Eq,
    "pi": sp.pi,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
    "sqrt": sp.sqrt,
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot, 
    "sec": sp.sec, 
    "csc": sp.csc,
    "acot": sp.acot, 
    "asec": sp.asec, 
    "acsc": sp.acsc,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "log": sp.log,
    "ln": sp.log,
    "exp": sp.exp,
    "Abs": sp.Abs,
    "Point": sp.Point,
    "Point3D": sp.Point3D,
    "Line": sp.Line,
    "Plane": sp.Plane,
    "Segment": sp.Segment,
    "Ray": sp.Ray,
    "Circle": sp.Circle,
    "Triangle": sp.Triangle,
    "Polygon": sp.Polygon,
    "RegularPolygon": sp.RegularPolygon,
    "intersection": sp.intersection,
    "Matrix": sp.Matrix,
    "eye": sp.eye,
    "zeros": sp.zeros,
    "ones": sp.ones,
    "diag": sp.diag,
    "Function": sp.Function,
    "Derivative": sp.Derivative,
    "dsolve": sp.dsolve,
    "factorial": sp.factorial,
    "binomial": sp.binomial,
    "nC": sp.binomial,
     "nP": lambda n, r: sp.factorial(n) / sp.factorial(n-r), # Permutations (nPr)
    # Pre-define functions y(x) and f(x) for Differential Equations
    "y": sp.Function('y'),
    "f": sp.Function('f'),
    
}

def get_all_locals() -> dict:
    combined = BASE_LOCALS.copy()
    for mod in MODULES: combined.update(getattr(mod, "SYMPY_LOCALS", {}))
    return combined

def get_all_rules() -> list[str]:
    return [rule for mod in MODULES for rule in getattr(mod, "RULES", [])]

def get_all_examples() -> list[str]:
    return [ex for mod in MODULES for ex in getattr(mod, "EXAMPLES", [])]

def execute_task(task, expr, variables, equations):
    for mod in MODULES:
        if hasattr(mod, "execute"):
            res = mod.execute(task, expr, variables, equations)
            if res is not None: return res
    return None

def get_solution_steps(task, expr_str, result) -> str | None:
    for mod in MODULES:
        if hasattr(mod, "get_steps"):
            steps = mod.get_steps(task, expr_str, result)
            if steps: return steps
    return None