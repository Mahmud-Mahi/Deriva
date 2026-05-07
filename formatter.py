import re
from typing import Any
import sympy as sp
from sympy.geometry.entity import GeometryEntity
from sympy.geometry import Point

# Expanded map to handle common variables in exponents to prevent crashes
SUPERSCRIPTS = str.maketrans(
    "-0123456789+=( )nxyzr", 
    "⁻⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁼⁽ ⁾ⁿˣʸᶻʳ"
)

SYMBOL_NAMES = {
    "pi": "π",
    "theta": "θ",
}

def normalize_equation_text(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("Eq("):
        return cleaned
    if "=" not in cleaned or any(operator in cleaned for operator in ("<=", ">=", "!=", "==")):
        return cleaned

    left, right = cleaned.split("=", 1)
    return f"Eq({left.strip()}, {right.strip()})"

def parse_math(text: str, local_dict: dict) -> sp.Basic:
    """
    Moved from main.py to formatter.py to break circular imports.
    Requires local_dict to be passed from the modules.
    """
    from sympy.parsing.sympy_parser import (
        convert_xor, 
        implicit_multiplication_application, 
        parse_expr, 
        standard_transformations
    )
    text = normalize_equation_text(text)
    transformations = standard_transformations + (convert_xor,)
    if "Function(" not in text and "Derivative(" not in text:
        transformations += (implicit_multiplication_application,)
    return parse_expr(
        text,
        local_dict=local_dict,
        global_dict={},
        transformations=transformations,
        evaluate=True,
    )

def inline_power(match: re.Match[str]) -> str:
    base = match.group("base")
    exponent = match.group("exponent")
    return f"{base}{exponent.translate(SUPERSCRIPTS)}"

def format_fraction_block(
    numerator_text: str, 
    denominator_text: str, 
    negative: bool = False
) -> str:
    width = max(len(numerator_text), len(denominator_text), 3)
    numerator_line = numerator_text.center(width)
    bar_line = "─" * width
    denominator_line = denominator_text.center(width)

    if negative:
        numerator_line = "-" + numerator_line
        bar_line = " " + bar_line
        denominator_line = " " + denominator_line

    return "\n".join([numerator_line, bar_line, denominator_line])

def format_fraction(value: sp.Rational) -> str:
    numerator, denominator = value.as_numer_denom()
    return format_fraction_block(
        str(abs(int(numerator))), 
        str(int(denominator)), 
        negative=numerator < 0
        )

def needs_parentheses(expr: sp.Basic) -> bool:
    return isinstance(expr, (sp.Add, sp.Equality))

def format_factor(expr: sp.Basic) -> str:
    text = inline_math(expr)
    return f"({text})" if needs_parentheses(expr) else text

def format_fraction_sum(expr: sp.Add) -> str | None:
    terms = expr.as_ordered_terms()
    if not any(term.as_coeff_Mul()[0].is_Rational and term.as_coeff_Mul()[0].q != 1 for term in terms):
        return None

    top_parts: list[str] = []
    bar_parts: list[str] = []
    bottom_parts: list[str] = []

    for index, term in enumerate(terms):
        negative = term.could_extract_minus_sign()
        positive_term = -term if negative else term
        coefficient, rest = positive_term.as_coeff_Mul()

        if coefficient.is_Rational and coefficient.q != 1:
            numerator_parts: list[str] = []
            if coefficient.p != 1 or rest == 1:
                numerator_parts.append(str(coefficient.p))
            if rest != 1:
                numerator_parts.append(format_factor(rest))
            numerator = "⋅".join(numerator_parts)
            denominator = str(coefficient.q)
        else:
            numerator = inline_math(positive_term)
            denominator = "1"

        width = max(len(numerator), len(denominator), 3)
        separator = " - " if negative else (" + " if index > 0 else "")
        top_parts.append(" " * len(separator) + numerator.center(width))
        bar_parts.append(separator + ("─" * width))
        bottom_parts.append(" " * len(separator) + denominator.center(width))

    return "\n".join([
        "".join(top_parts), 
        "".join(bar_parts), 
        "".join(bottom_parts)
    ])

def format_equality(value: sp.Equality) -> str:
    lhs = inline_math(value.lhs)
    rhs = inline_math(value.rhs)
    
    lhs_lines = lhs.splitlines()
    rhs_lines = rhs.splitlines()

    if len(lhs_lines) == 1 and len(rhs_lines) == 1:
        return f"{lhs} = {rhs}"

    if len(lhs_lines) == 1:
        prefix = f"{lhs} = "
        continuation = " " * len(prefix)
        if len(rhs_lines) == 3:
            return "\n".join([
                continuation + rhs_lines[0], 
                prefix + rhs_lines[1], 
                continuation + rhs_lines[2]])
        return "\n".join([
            prefix + rhs_lines[0], 
            *[continuation + line for line in rhs_lines[1:]]
        ])

    return "\n".join(lhs_lines + ["="] + rhs_lines)

def format_matrix(mat: Any) -> str:
    if mat.rows == 0 or mat.cols == 0:
        return "[]"
        
    formatted_rows = [[inline_math(cell) for cell in row] for row in mat.tolist()]
    col_widths = [max(len(row[c]) for row in formatted_rows) for c in range(mat.cols)]
    
    lines = []
    for r_idx, row in enumerate(formatted_rows):
        cells = [cell.rjust(col_widths[c]) for c, cell in enumerate(row)]
        content = "  ".join(cells)
        if mat.rows == 1: 
            lines.append(f"[ {content} ]")
        elif r_idx == 0: 
            lines.append(f"⎡ {content} ⎤")
        elif r_idx == mat.rows - 1: 
            lines.append(f"⎣ {content} ⎦")
        else: 
            lines.append(f"⎢ {content} ⎥")

    return "\n".join(lines)

def prefix_first_line(text: str, prefix: str) -> str:
    lines = text.splitlines()
    if not lines: 
        return prefix
    lines[0] = prefix + lines[0]
    continuation_prefix = " " * len(prefix)
    return "\n".join([lines[0], *[continuation_prefix + line for line in lines[1:]]])

def format_add(expr: sp.Add) -> str:
    fraction_sum = format_fraction_sum(expr)
    if fraction_sum is not None:
        return fraction_sum

    pieces: list[str] = []
    for term in expr.as_ordered_terms():
        negative = term.could_extract_minus_sign()
        positive_term = -term if negative else term
        term_text = inline_math(positive_term)

        if not pieces: 
            pieces.append(prefix_first_line(term_text, "-") if negative else term_text)
        else: 
            pieces.append(prefix_first_line(term_text, " - " if negative else " + "))
    
    return "".join(pieces)

def format_mul(expr: sp.Mul) -> str:
    coefficient, rest = expr.as_coeff_Mul()
    factors = list(rest.as_ordered_factors()) if rest != 1 else []

    if coefficient == -1 and factors:
        return "-" + "⋅".join(format_factor(factor) for factor in factors)

    if isinstance(coefficient, sp.Rational) and coefficient.q != 1:
        numerator_parts: list[str] = []
        numerator_abs = abs(int(coefficient.p))
        if numerator_abs != 1 or not factors:
            numerator_parts.append(str(numerator_abs))
        numerator_parts.extend(format_factor(factor) for factor in factors)
        numerator_text = "⋅".join(numerator_parts)
        if len(numerator_parts) > 1: 
            numerator_text = f"({numerator_text})"
        return format_fraction_block(
            numerator_text, 
            str(int(coefficient.q)), 
            negative=coefficient < 0
        )

    pieces: list[str] = []
    if coefficient != 1 or not factors: 
        pieces.append(inline_math(coefficient))
    
    pieces.extend(format_factor(factor) for factor in factors)
    return "⋅".join(piece for piece in pieces if piece)

def fallback_inline_math(value: Any) -> str:
    text = sp.sstr(value)
    text = text.replace("log", "ln")
    text = re.sub(
        r"(?P<base>[A-Za-z0-9_]+|\([^()]+\))\*\*(?P<exponent>-?[A-Za-z0-9_]+|\([^()]+\))", 
        inline_power, 
        text
    )
    text = re.sub(r"sqrt\(([^()]+)\)", r"√(\1)", text)
    text = re.sub(r"Abs\(([^()]+)\)", r"|\1|", text)
    text = text.replace("*", "⋅")
    text = text.replace("pi", "π")
    return text

def inline_math(value: Any) -> str:
    if getattr(value, "is_Matrix", False): 
        return format_matrix(value)
    
    if isinstance(value, list) and len(value) == 1:
        value = value[0]
        
    if isinstance(value, sp.Derivative):
        var = value.variables[0]
        func = value.expr
        return f"d/d{pretty_math(var)}({pretty_math(func)})"
    
    if isinstance(value, Point):
        if len(value.args) == 2:
            return f"({inline_math(value.args[0])}, {inline_math(value.args[1])})"
        return f"Point({', '.join(inline_math(a) for a in value.args)})"
    
    if isinstance(value, GeometryEntity):
        name = value.__class__.__name__.replace("2D", "").replace("3D", "")
        args = ", ".join(inline_math(arg) for arg in value.args)
        return f"{name}({args})"
    
    if isinstance(value, dict):
        return "{" + ", ".join(
            f"{inline_math(key)}: {inline_math(item)}" for key, item in value.items()
        ) + "}"

    if isinstance(value, (list, tuple, set)):
        items = [inline_math(item) for item in value]
        left, right = ("{", "}") if isinstance(value, set) else ("[", "]")
        if any("\n" in item for item in items):
            return left + ",\n".join(items) + right
        return left + ", ".join(items) + right
    
    if isinstance(value, sp.Equality): 
        return format_equality(value)
    if isinstance(value, sp.Symbol): 
        return SYMBOL_NAMES.get(str(value), str(value))
    if isinstance(value, sp.Rational): 
        return str(value.p) if value.q == 1 else format_fraction(value)
    if isinstance(value, sp.Float): 
        return str(value)
    if value == sp.pi: 
        return "π"
    if isinstance(value, sp.Add): 
        return format_add(value)
    if isinstance(value, sp.Mul): 
        return format_mul(value)
    if isinstance(value, sp.Pow):
        base, exponent = value.as_base_exp()
        if exponent == sp.Rational(1, 2): 
            return f"√({inline_math(base)})"
        if exponent.is_Integer or isinstance(exponent, sp.Symbol): 
            return f"{format_factor(base)}{str(exponent).translate(SUPERSCRIPTS)}"
    if isinstance(value, sp.Function):
        if value.func == sp.log: 
            return f"ln({inline_math(value.args[0])})"
        if value.func == sp.Abs: 
            return f"|{inline_math(value.args[0])}|"
        if value.func == sp.binomial: 
            return f"C({inline_math(value.args[0])}, {inline_math(value.args[1])})"
        args = ", ".join(inline_math(arg) for arg in value.args)
        return f"{value.func.__name__}({args})"
    
    return fallback_inline_math(value)

def pretty_math(value: Any) -> str: 
    return inline_math(value)

def indented_math(value: Any, spaces: int = 3) -> str: 
    return "\n".join(f"{' ' * spaces}{line}" for line in pretty_math(value).splitlines())

def add_step_breaks(text: str) -> str: 
    return re.sub(r"\n(?=\d+\. )", "\n\n", text)
