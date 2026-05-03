import sympy as sp
import re
from typing import Any
from models import MathTask
from formatter import indented_math, parse_math

SYMPY_LOCALS = {
    "factorial": sp.factorial,
    "binomial": sp.binomial,
    "nC": sp.binomial,
    "nP": lambda n, r: sp.factorial(n) / sp.factorial(n-r)
}

RULES = [
    "For COMBINATORICS: Use nP(n, r) for permutations and nC(n, r) for combinations.",
    "For IDENTICAL ITEMS (Multisets): Use factorial(n) / (factorial(k1) * factorial(k2)...).",
    "For CIRCULAR PERMUTATIONS: Use factorial(n - 1).",
    "For SELECTION WITH REPLACEMENT (Stars and Bars): Use nC(n + k - 1, k - 1)."
]

EXAMPLES = [
    'User problem: Ways to choose 3 from 10\nJSON: {"operation":"evaluate","expression":"nC(10, 3)"}',
    'User problem: Ways to arrange the letters in "BANANA"\nJSON: {"operation":"evaluate","expression":"factorial(6) / (factorial(3) * factorial(2))"}'
]

def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    # Combinatorics usually just requires evaluation of the expression
    if task.operation == "evaluate":
        return sp.simplify(expr)
    return None

def get_steps(task: MathTask, expr_str: str, result: Any):
    if task.operation != "evaluate":
        return None

    lines = []
    
    # 1. Standard nPr or nCr
    match = re.search(r"n([PC])\s*\(\s*([^,]+),\s*([^)]+)\)", expr_str)
    if match:
        ctype, n, r = match.groups()
        is_perm = (ctype == 'P')
        lines.append(f"1. We are calculating {'Permutations' if is_perm else 'Combinations'}.")
        lines.append(f"   n (total items) = {n}")
        lines.append(f"   r (items to select) = {r}")
        lines.append(f"2. Formula: {'n! / (n - r)!' if is_perm else 'n! / (r! ⋅ (n - r)!)'}")
        lines.append("3. The calculated result is:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    # 2. Multiset Permutations (Arranging items with repeats)
    if "/" in expr_str and "factorial" in expr_str:
        lines.append("1. This is a permutation of a multiset (items with repetitions).")
        lines.append("2. The formula is: n! / (k₁! ⋅ k₂! ⋅ ... ⋅ kₘ!)")
        lines.append("   where n is the total number of items, and k represents the frequency of each identical item.")
        lines.append("3. Plugging in the counts and calculating:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    # 3. Circular Permutations
    if "factorial" in expr_str and "- 1" in expr_str:
        lines.append("1. This is a circular permutation problem.")
        lines.append("2. Since the arrangement is in a circle, we fix one item to break the symmetry.")
        lines.append("3. The formula is: (n - 1)!")
        lines.append("4. Result:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    # 4. Basic Factorials
    if "factorial" in expr_str:
        lines.append("1. This is a simple permutation problem (arranging all distinct items).")
        lines.append("2. Formula: n!")
        lines.append("3. Result:")
        lines.append(indented_math(result))
        return "\n".join(lines)

    # Default fallback for evaluation
    lines.extend([
        "1. Analyze the counting principle required (Multiplication principle or Factorials).",
        "2. The final number of ways is:",
        indented_math(result)
    ])
    return "\n".join(lines)