from typing import Any

import sympy as sp

from formatter import indented_math
from models import MathTask


lamda = sp.Symbol("λ")


def _as_matrix(value) -> sp.Matrix:
    return value if isinstance(value, sp.MatrixBase) else sp.Matrix(value)


def matrix_add(a, b):
    return _as_matrix(a) + _as_matrix(b)


def matrix_subtract(a, b):
    return _as_matrix(a) - _as_matrix(b)


def matrix_multiply(a, b):
    return _as_matrix(a) * _as_matrix(b)


def scalar_multiply(k, a):
    return sp.sympify(k) * _as_matrix(a)


def matrix_power(a, n):
    return _as_matrix(a) ** sp.sympify(n)


def matrix_transpose(a):
    return _as_matrix(a).T


def determinant(a):
    return _as_matrix(a).det()


def minor(a, row, col):
    return _as_matrix(a).minor(int(row), int(col))


def cofactor(a, row, col):
    return _as_matrix(a).cofactor(int(row), int(col))


def minors_matrix(a):
    matrix = _as_matrix(a)
    return sp.Matrix(matrix.rows, matrix.cols, lambda i, j: matrix.minor(i, j))


def cofactor_matrix(a):
    return _as_matrix(a).cofactor_matrix()


def adjoint(a):
    return _as_matrix(a).adjugate()


def inverse(a):
    return _as_matrix(a).inv()


def inverse_by_adjoint(a):
    matrix = _as_matrix(a)
    det = matrix.det()
    if det == 0:
        raise ValueError("Matrix is singular; inverse does not exist.")
    return sp.simplify(matrix.adjugate() / det)


def matrix_rank(a):
    return _as_matrix(a).rank()


def row_echelon(a):
    return _as_matrix(a).echelon_form()


def reduced_row_echelon(a):
    rref_matrix, pivots = _as_matrix(a).rref()
    return {"rref": rref_matrix, "pivots": sp.Tuple(*pivots)}


def trace(a):
    return _as_matrix(a).trace()


def is_symmetric(a):
    matrix = _as_matrix(a)
    return matrix == matrix.T


def is_skew_symmetric(a):
    matrix = _as_matrix(a)
    return matrix == -matrix.T


def symmetric_part(a):
    matrix = _as_matrix(a)
    return sp.simplify((matrix + matrix.T) / 2)


def skew_symmetric_part(a):
    matrix = _as_matrix(a)
    return sp.simplify((matrix - matrix.T) / 2)


def matrix_type(a):
    matrix = _as_matrix(a)
    return {
        "order": (matrix.rows, matrix.cols),
        "square": matrix.rows == matrix.cols,
        "symmetric": is_symmetric(matrix) if matrix.rows == matrix.cols else False,
        "skew_symmetric": is_skew_symmetric(matrix) if matrix.rows == matrix.cols else False,
        "diagonal": matrix.is_diagonal() if matrix.rows == matrix.cols else False,
        "identity": matrix == sp.eye(matrix.rows) if matrix.rows == matrix.cols else False,
        "zero": matrix == sp.zeros(matrix.rows, matrix.cols),
    }


def solve_matrix_equation_left(a, b):
    # Solves A X = B
    return _as_matrix(a).inv() * _as_matrix(b)


def solve_matrix_equation_right(a, b):
    # Solves X A = B
    return _as_matrix(b) * _as_matrix(a).inv()


def solve_linear_system_matrix(a, b):
    return _as_matrix(a).gauss_jordan_solve(_as_matrix(b))[0]


def cramer_solution(a, b):
    matrix = _as_matrix(a)
    rhs = _as_matrix(b)
    det_a = matrix.det()
    if det_a == 0:
        raise ValueError("Cramer's rule requires a non-zero determinant.")
    values = []
    for col in range(matrix.cols):
        replaced = matrix.copy()
        replaced[:, col] = rhs
        values.append(sp.simplify(replaced.det() / det_a))
    return sp.Matrix(values)


def system_consistency(a, b):
    matrix = _as_matrix(a)
    rhs = _as_matrix(b)
    augmented = matrix.row_join(rhs)
    rank_a = matrix.rank()
    rank_aug = augmented.rank()
    if rank_a != rank_aug:
        status = "inconsistent"
    elif rank_a == matrix.cols:
        status = "unique solution"
    else:
        status = "infinitely many solutions"
    return {"rank_A": rank_a, "rank_augmented": rank_aug, "status": status}


def characteristic_polynomial(a, symbol=lamda):
    return _as_matrix(a).charpoly(symbol).as_expr()


def characteristic_equation(a, symbol=lamda):
    return sp.Eq(characteristic_polynomial(a, symbol), 0, evaluate=False)


def eigen_values(a):
    return _as_matrix(a).eigenvals()


def eigen_vectors(a):
    return sp.Tuple(*(
        sp.Tuple(value, multiplicity, sp.Tuple(*vectors))
        for value, multiplicity, vectors in _as_matrix(a).eigenvects()
    ))


def cayley_hamilton(a, symbol=lamda):
    matrix = _as_matrix(a)
    poly = matrix.charpoly(symbol).as_expr()
    coeffs = sp.Poly(poly, symbol).all_coeffs()
    value = sp.zeros(matrix.rows)
    degree = len(coeffs) - 1
    for index, coeff in enumerate(coeffs):
        power = degree - index
        value += coeff * (matrix ** power if power else sp.eye(matrix.rows))
    return {"characteristic_polynomial": poly, "p_of_A": sp.simplify(value)}


def diagonalize_matrix(a):
    p, d = _as_matrix(a).diagonalize()
    return {"P": p, "D": d}


def matrix_from_columns(*columns):
    return sp.Matrix.hstack(*(_as_matrix(column) for column in columns))


def matrix_from_rows(*rows):
    return sp.Matrix.vstack(*(_as_matrix(row).T if _as_matrix(row).cols == 1 else _as_matrix(row) for row in rows))


def area_triangle_determinant(point1, point2, point3):
    x1, y1 = point1
    x2, y2 = point2
    x3, y3 = point3
    det = sp.Matrix([[x1, y1, 1], [x2, y2, 1], [x3, y3, 1]]).det()
    return sp.Abs(det) / 2


def are_points_collinear(point1, point2, point3):
    return sp.simplify(area_triangle_determinant(point1, point2, point3)) == 0


SYMPY_LOCALS = {
    "Matrix": sp.Matrix,
    "eye": sp.eye,
    "zeros": sp.zeros,
    "ones": sp.ones,
    "diag": sp.diag,
    "lamda": lamda,
    "matrix_add": matrix_add,
    "matrix_subtract": matrix_subtract,
    "matrix_multiply": matrix_multiply,
    "scalar_multiply": scalar_multiply,
    "matrix_power": matrix_power,
    "matrix_transpose": matrix_transpose,
    "determinant": determinant,
    "minor": minor,
    "cofactor": cofactor,
    "minors_matrix": minors_matrix,
    "cofactor_matrix": cofactor_matrix,
    "adjoint": adjoint,
    "inverse": inverse,
    "inverse_by_adjoint": inverse_by_adjoint,
    "matrix_rank": matrix_rank,
    "row_echelon": row_echelon,
    "reduced_row_echelon": reduced_row_echelon,
    "trace": trace,
    "is_symmetric": is_symmetric,
    "is_skew_symmetric": is_skew_symmetric,
    "symmetric_part": symmetric_part,
    "skew_symmetric_part": skew_symmetric_part,
    "matrix_type": matrix_type,
    "solve_matrix_equation_left": solve_matrix_equation_left,
    "solve_matrix_equation_right": solve_matrix_equation_right,
    "solve_linear_system_matrix": solve_linear_system_matrix,
    "cramer_solution": cramer_solution,
    "system_consistency": system_consistency,
    "characteristic_polynomial": characteristic_polynomial,
    "characteristic_equation": characteristic_equation,
    "eigen_values": eigen_values,
    "eigen_vectors": eigen_vectors,
    "cayley_hamilton": cayley_hamilton,
    "diagonalize_matrix": diagonalize_matrix,
    "matrix_from_columns": matrix_from_columns,
    "matrix_from_rows": matrix_from_rows,
    "area_triangle_determinant": area_triangle_determinant,
    "are_points_collinear": are_points_collinear,
}

RULES = [
    "For MATRICES: use Matrix([[...], [...]]) syntax.",
    "For matrix operations: use matrix_add(A,B), matrix_subtract(A,B), matrix_multiply(A,B), scalar_multiply(k,A), matrix_power(A,n), matrix_transpose(A).",
    "For DETERMINANTS: use determinant(A), minor(A,row,col), cofactor(A,row,col), minors_matrix(A), cofactor_matrix(A), adjoint(A). Row/column indices are 0-based.",
    "For INVERSES: use inverse(A) or inverse_by_adjoint(A).",
    "For RANK and row reduction: use matrix_rank(A), row_echelon(A), reduced_row_echelon(A).",
    "For SYMMETRIC/SKEW matrices: use is_symmetric(A), is_skew_symmetric(A), symmetric_part(A), skew_symmetric_part(A), matrix_type(A).",
    "For MATRIX EQUATIONS: use solve_matrix_equation_left(A,B) for AX=B and solve_matrix_equation_right(A,B) for XA=B.",
    "For LINEAR SYSTEMS: use solve_linear_system_matrix(A,B), cramer_solution(A,B), or system_consistency(A,B).",
    "For CHARACTERISTIC/EIGEN/Cayley-Hamilton: use characteristic_polynomial(A), characteristic_equation(A), eigen_values(A), eigen_vectors(A), cayley_hamilton(A).",
    "For determinant geometry: use area_triangle_determinant((x1,y1),(x2,y2),(x3,y3)) or are_points_collinear(...).",
]

EXAMPLES = [
    'User problem: inverse of [[1, 2], [3, 4]]\nJSON: {"operation":"evaluate","expression":"inverse(Matrix([[1, 2], [3, 4]]))"}',
    'User problem: determinant of [[1,2],[3,4]]\nJSON: {"operation":"evaluate","expression":"determinant(Matrix([[1, 2], [3, 4]]))"}',
    'User problem: adjoint of [[1,2],[3,4]]\nJSON: {"operation":"evaluate","expression":"adjoint(Matrix([[1, 2], [3, 4]]))"}',
    'User problem: solve AX=B where A=[[2,1],[1,-1]] and B=[[5],[1]]\nJSON: {"operation":"evaluate","expression":"solve_matrix_equation_left(Matrix([[2, 1], [1, -1]]), Matrix([[5], [1]]))"}',
    'User problem: rank of [[1,2,3],[2,4,6]]\nJSON: {"operation":"evaluate","expression":"matrix_rank(Matrix([[1, 2, 3], [2, 4, 6]]))"}',
    'User problem: characteristic equation of [[1,2],[2,1]]\nJSON: {"operation":"evaluate","expression":"characteristic_equation(Matrix([[1, 2], [2, 1]]))"}',
    'User problem: verify Cayley Hamilton for [[1,2],[2,1]]\nJSON: {"operation":"evaluate","expression":"cayley_hamilton(Matrix([[1, 2], [2, 1]]))"}',
    'User problem: area of triangle with points (0,0), (4,0), (0,3)\nJSON: {"operation":"evaluate","expression":"area_triangle_determinant((0, 0), (4, 0), (0, 3))"}',
]

MATRIX_MARKERS = (
    "Matrix(",
    "eye(",
    "zeros(",
    "ones(",
    "diag(",
    ".det(",
    ".inv(",
    ".T",
    "eigenvals",
    "eigenvects",
    "matrix_",
    "determinant(",
    "minor(",
    "cofactor(",
    "adjoint(",
    "inverse(",
    "inverse_by_adjoint(",
    "row_echelon(",
    "reduced_row_echelon(",
    "trace(",
    "is_symmetric(",
    "is_skew_symmetric(",
    "symmetric_part(",
    "skew_symmetric_part(",
    "solve_matrix_equation_",
    "solve_linear_system_matrix(",
    "cramer_solution(",
    "system_consistency(",
    "characteristic_",
    "eigen_values(",
    "eigen_vectors(",
    "cayley_hamilton(",
    "diagonalize_matrix(",
    "matrix_from_columns(",
    "matrix_from_rows(",
    "area_triangle_determinant(",
    "are_points_collinear(",
)


def is_matrix_task(task: MathTask, expr: Any) -> bool:
    expr_text = task.expression or task.equation or ""
    return isinstance(expr, sp.MatrixBase) or any(marker in expr_text for marker in MATRIX_MARKERS)


def execute(task: MathTask, expr: sp.Basic, variables: list, equations: list):
    if task.operation == "evaluate" and is_matrix_task(task, expr):
        try:
            res = expr.doit() if hasattr(expr, "doit") else expr
            if isinstance(res, sp.MatrixBase):
                res.simplify()
                return res
            if isinstance(res, (dict, sp.Tuple, list, bool, str)):
                return res
            if hasattr(res, "simplify"):
                return res.simplify()
            return res
        except Exception as e:
            return f"Matrix Error: {str(e)}"
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if task.operation != "evaluate" or not is_matrix_task(task, result):
        return None

    step_map = [
        ("reduced_row_echelon(", "1. Use elementary row operations to reach reduced row echelon form."),
        ("inverse_by_adjoint(", "1. Use A⁻¹ = adj(A) / det(A), provided det(A) is non-zero."),
        ("skew_symmetric_part(", "1. Use (A - Aᵀ) / 2."),
        ("area_triangle_determinant(", "1. Use the determinant formula for area of a triangle."),
        ("are_points_collinear(", "1. Points are collinear when the determinant area is zero."),
        ("matrix_from_columns(", "1. Place the given column vectors side by side."),
        ("matrix_from_rows(", "1. Stack the given row vectors one below another."),
        ("matrix_add(", "1. Add corresponding entries of the two matrices."),
        ("matrix_subtract(", "1. Subtract corresponding entries of the two matrices."),
        ("matrix_multiply(", "1. Multiply rows of the first matrix by columns of the second matrix."),
        ("scalar_multiply(", "1. Multiply every entry of the matrix by the scalar."),
        ("matrix_power(", "1. Repeatedly multiply the matrix by itself."),
        ("matrix_transpose(", "1. Interchange rows and columns."),
        ("determinant(", "1. Compute the determinant using expansion or row operations."),
        (".det(", "1. Compute the determinant using expansion or row operations."),
        ("minor(", "1. Delete the selected row and column, then take the determinant."),
        ("cofactor(", "1. Multiply the minor by (-1)^(i+j)."),
        ("minors_matrix(", "1. Compute each minor entry by entry."),
        ("cofactor_matrix(", "1. Compute the cofactor of each entry."),
        ("adjoint(", "1. Compute the cofactor matrix and transpose it."),
        ("inverse(", "1. Find the inverse using row reduction or the adjoint formula."),
        (".inv(", "1. Find the inverse using row reduction or the adjoint formula."),
        ("matrix_rank(", "1. Reduce the matrix and count the non-zero rows/pivots."),
        ("row_echelon(", "1. Use elementary row operations to reach echelon form."),
        ("trace(", "1. Add the main diagonal entries."),
        ("is_symmetric(", "1. Check whether A equals its transpose."),
        ("is_skew_symmetric(", "1. Check whether A equals the negative of its transpose."),
        ("symmetric_part(", "1. Use (A + Aᵀ) / 2."),
        ("matrix_type(", "1. Check order and special matrix properties."),
        ("solve_matrix_equation_left(", "1. For AX=B, multiply by A⁻¹ on the left."),
        ("solve_matrix_equation_right(", "1. For XA=B, multiply by A⁻¹ on the right."),
        ("solve_linear_system_matrix(", "1. Write the system as AX=B and solve by elimination."),
        ("cramer_solution(", "1. Use Cramer's rule: replace one column at a time and divide by det(A)."),
        ("system_consistency(", "1. Compare rank(A) and rank([A|B])."),
        ("characteristic_polynomial(", "1. Compute det(λI - A)."),
        ("characteristic_equation(", "1. Set the characteristic polynomial equal to zero."),
        ("eigen_values(", "1. Solve the characteristic equation for eigenvalues."),
        ("eigen_vectors(", "1. For each eigenvalue, solve (A-λI)X=0."),
        ("cayley_hamilton(", "1. Compute the characteristic polynomial p(λ), then evaluate p(A)."),
        ("diagonalize_matrix(", "1. Find P and D such that A = PDP⁻¹."),
    ]

    for marker, first_step in step_map:
        if marker in expr_str:
            return "\n".join([
                first_step,
                "2. Substitute the given matrix entries and simplify.",
                "3. The result is:",
                indented_math(result),
            ])

    if "*" in expr_str and "Matrix" in expr_str:
        return "\n".join([
            "1. Matrix multiplication is defined row-by-column.",
            "2. Check that the dimensions are compatible.",
            "3. The product is:",
            indented_math(result),
        ])

    return "\n".join([
        "1. Perform the requested matrix operation.",
        "2. Simplify the resulting entries.",
        "3. The result is:",
        indented_math(result),
    ])
