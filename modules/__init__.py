from . import (
    algebra,
    calculus,
    circle,
    combination,
    conics,
    matrix,
    shared,
    straight_line,
    trigonometry,
    vector,
)
import sympy as sp

# Topic mapping for direct module routing
TOPIC_TO_MODULE = {
    "algebra": algebra,
    "geometry": shared,
    "conics": conics,
    "circle": circle,
    "line": straight_line,
    "straight-line": straight_line,
    "straight_line": straight_line,
    "permutation": combination,
    "combination": combination,
    "permutation_combination": combination,
    "vector": vector,
    "matrix": matrix,
    "calculus": calculus,
    "trig": trigonometry,
    "trigonometry": trigonometry,
    "inverse_trigonometry": trigonometry,
    "inverse-trigonometry": trigonometry,
}

MODULES = [
    shared,
    vector,
    circle,
    straight_line,
    conics,
    matrix,
    trigonometry,
    algebra,
    calculus,
    combination,
]

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


# --- Topic Parsing and Routing ---

def parse_topic_prefix(user_input: str) -> tuple[str | None, str]:
    """
    Parse user input for topic prefixes like '/vector' or '#algebra'.
    Returns (topic, cleaned_input) or (None, user_input) if no prefix found.
    """
    import re
    # Match topics like /vector, #algebra, vector:, etc.
    pattern = r'^[/#](\w[\w-]*)(?:[:,]|\s+)(.*)'
    match = re.match(pattern, user_input.strip(), re.IGNORECASE)
    if match:
        topic = match.group(1).lower()
        content = match.group(2)
        return topic, content.strip()
    return None, user_input


def get_module_for_topic(topic: str):
    """Get the module for a given topic name."""
    return TOPIC_TO_MODULE.get(topic.lower())


def execute_topic_task(topic: str, problem: str, model: str, url: str):
    """
    Execute a problem using only the specified topic's module.
    Bypasses the default multi-module dispatch.
    """
    from models import MathTask
    from formatter import parse_math

    topic_lower = topic.lower()
    module = TOPIC_TO_MODULE.get(topic_lower)

    if not module:
        raise ValueError(f"Unknown topic: {topic}. Available topics: {', '.join(TOPIC_TO_MODULE.keys())}")

    # Get module-specific rules and examples for the LLM
    rules = "\n".join(f"- {rule}" for rule in getattr(module, "RULES", []))
    examples = "\n\n".join(getattr(module, "EXAMPLES", []))

    # Build prompt with module-specific context
    prompt = f"Convert to SymPy JSON (using {topic_lower} module):\nRules:\n{rules}\nExamples:\n{examples}\nProblem: {problem}"

    import urllib.request
    import json as json_module

    DEFAULT_MODEL = model
    DEFAULT_OLLAMA_URL = url

    def ask_ollama_local(prompt_text: str, model_str: str, url_str: str) -> str:
        payload = {
            "model": model_str,
            "prompt": prompt_text,
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.0,
                "num_predict": 128,
            },
        }

        request = urllib.request.Request(
            url_str,
            data=json_module.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                resp_data = json_module.loads(response.read().decode("utf-8"))
                return resp_data.get("response", "").strip()
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}")

    last_error = None
    for attempt in range(3):
        raw = ask_ollama_local(prompt, DEFAULT_MODEL, DEFAULT_OLLAMA_URL)

        try:
            data = json_module.loads(raw)
        except json_module.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw[start:end + 1]
                try:
                    data = json_module.loads(candidate)
                except Exception:
                    data = None
            else:
                data = None

        if isinstance(data, dict) and "operation" in data:
            task = MathTask(**data)

            # Parse the expression using module-specific context
            locals_dict = get_all_locals()
            expr = parse_math(task.expression or task.equation or "0", locals_dict)
            if isinstance(expr, list) and len(expr) > 0:
                expr = expr[0]

            raw_eqs = task.equations or ([task.equation] if task.equation else [])
            equations = []
            for e in raw_eqs:
                parsed_e = parse_math(e, locals_dict)
                if isinstance(parsed_e, list) and len(parsed_e) > 0:
                    parsed_e = parsed_e[0]
                equations.append(parsed_e)

            provided_vars = task.variables or ([task.variable] if task.variable else [])
            all_free_symbols = set(getattr(expr, "free_symbols", set()))
            for eq in equations:
                all_free_symbols.update(getattr(eq, "free_symbols", set()))

            if not provided_vars or (len(provided_vars) == 1 and provided_vars[0] == 'x' and sp.Symbol('x') not in all_free_symbols):
                if all_free_symbols:
                    variables = sorted(list(all_free_symbols), key=lambda s: s.name)
                    task.variables = [v.name for v in variables]
                    task.variable = variables[0].name
                else:
                    variables = [sp.Symbol('x')]
            else:
                variables = [sp.Symbol(v) for v in provided_vars]

            # Execute using only the topic's module
            result = module.execute(task, expr, variables, equations)
            if result is not None:
                return task, expr, variables, equations, result, module

            # Fallback to generic sympy solve
            if task.operation == "solve":
                result = sp.solve(equations or [expr], variables, dict=len(variables) > 1)
            else:
                result = sp.simplify(expr)
            return task, expr, variables, equations, result, module

        last_error = last_error or RuntimeError("missing operation in returned task JSON")
        prompt = (
            "Return ONLY valid JSON for the MathTask. No markdown, no extra text.\n"
            f"Problem: {problem}\n"
            f"Rules:\n{rules}\n"
            f"Examples:\n{examples}\n"
        )

    raise RuntimeError(f"Failed to get valid task JSON from Ollama: {last_error}")
