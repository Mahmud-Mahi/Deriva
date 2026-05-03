import sympy as sp
from typing import Any
from models import MathTask
from formatter import indented_math, inline_math, parse_math

SYMPY_LOCALS = {
    "Matrix": sp.Matrix, 
    "eye": sp.eye, 
    "zeros": sp.zeros, 
    "ones": sp.ones, 
    "diag": sp.diag,
    "lamda": sp.Symbol('λ')
}

RULES = [
    "For MATRICES: Use Matrix([[a, b], [c, d]]) syntax.",
    "For DETERMINANTS: Use matrix_obj.det().",
    "For INVERSES: Use matrix_obj.inv().",
    "For EIGENVALUES: Use matrix_obj.eigenvals() or matrix_obj.eigenvects().",
    "For VECTOR OPS: Use v1.cross(v2) or v1.dot(v2)."
]

EXAMPLES = [
    'User problem: inverse of [[1, 2], [3, 4]]\nJSON: {"operation":"evaluate","expression":"Matrix([[1, 2], [3, 4]]).inv()"}',
    'User problem: eigenvalues of [[1, 2], [2, 1]]\nJSON: {"operation":"evaluate","expression":"Matrix([[1, 2], [2, 1]]).eigenvals()"}'
]

def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if task.operation == "evaluate":
        try:
            # Matrices often need simplification after operations like inversion or multiplication
            res = expr.doit() if hasattr(expr, "doit") else expr
            if hasattr(res, "simplify"):
                return res.simplify()
            return res
        except Exception as e:
            return f"Matrix Error: {str(e)}"
    return None

def get_steps(task: MathTask, expr_str: str, result: Any):
    lines = []
    
    if task.operation == "evaluate":
        # Case 1: Determinant
        if ".det(" in expr_str or expr_str.endswith(".det()"):
            lines.extend([
                "1. To find the determinant, use cofactor expansion along a row or column.",
                "2. For a 2x2 matrix [[a, b], [c, d]], the formula is (ad - bc).",
                "3. The determinant is:", indented_math(result)
            ])
            return "\n".join(lines)

        # Case 2: Inverse
        if ".inv(" in expr_str or expr_str.endswith(".inv()"):
            lines.extend([
                "1. First, check if the determinant is non-zero (matrix must be non-singular).",
                "2. Use the Gauss-Jordan elimination method or the Adjugate matrix formula:",
                "   A⁻¹ = (1/det(A)) * adj(A)",
                "3. The resulting inverse matrix is:", indented_math(result)
            ])
            return "\n".join(lines)

        # Case 3: Eigenvalues
        if "eigenvals" in expr_str:
            lines.extend([
                "1. To find eigenvalues (λ), solve the characteristic equation: det(A - λI) = 0.",
                "2. This yields a polynomial in λ whose roots are the eigenvalues.",
                "3. The eigenvalues (and their multiplicities) are:", indented_math(result)
            ])
            return "\n".join(lines)

        # Case 4: Multiplication
        if "*" in expr_str and "Matrix" in expr_str:
            lines.extend([
                "1. Matrix multiplication is defined as the dot product of rows and columns.",
                "2. Ensure the number of columns in the first matrix equals the number of rows in the second.",
                "3. Perform the row-by-column summation.",
                "4. The product matrix is:", indented_math(result)
            ])
            return "\n".join(lines)

        # Case 5: Vector Cross Product
        if ".cross(" in expr_str:
            lines.extend([
                "1. Set up the vector cross product using the determinant of a 3x3 matrix.",
                "2. The top row consists of unit vectors i, j, k.",
                "3. The result is a vector orthogonal to both inputs:", indented_math(result)
            ])
            return "\n".join(lines)

        # Default Matrix Evaluation
        lines.extend([
            "1. Perform the matrix operation as defined (addition, subtraction, or scalar multiplication).",
            "2. Result:", indented_math(result)
        ])
        return "\n".join(lines)

    return None