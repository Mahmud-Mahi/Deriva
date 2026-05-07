from typing import Any

import sympy as sp

from formatter import indented_math
from models import MathTask


class Vector(sp.Matrix):
    def __new__(cls, components):
        return super().__new__(cls, components)

    def magnitude(self):
        return self.norm()

    def normalize(self):
        norm = self.norm()
        return self if norm == 0 else self / norm

    def angle_with(self, other):
        return angle_between(self, other)

    def projection_onto(self, other):
        return projection(self, other)

    def scalar_projection_onto(self, other):
        return scalar_projection(self, other)


def _as_vector(value) -> sp.Matrix:
    if isinstance(value, sp.MatrixBase):
        return value
    return Vector(value)


def _require_same_dimension(v1: sp.Matrix, v2: sp.Matrix) -> None:
    if v1.rows != v2.rows:
        raise ValueError("Vector dimensions must match.")


def _require_nonzero(vector: sp.Matrix, label: str = "vector") -> None:
    if sp.simplify(vector.dot(vector)) == 0:
        raise ValueError(f"The {label} must be non-zero.")


def magnitude(vector):
    return _as_vector(vector).norm()


def unit_vector(vector):
    vector = _as_vector(vector)
    _require_nonzero(vector)
    return sp.simplify(vector / vector.norm())


def angle_between(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    _require_nonzero(v1, "first vector")
    _require_nonzero(v2, "second vector")
    cosine = sp.simplify(v1.dot(v2) / (v1.norm() * v2.norm()))
    return sp.acos(cosine)


def scalar_projection(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    _require_nonzero(v2, "projection direction")
    return sp.simplify(v1.dot(v2) / v2.norm())


def projection(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    denominator = sp.simplify(v2.dot(v2))
    if denominator == 0:
        raise ValueError("Projection direction must be non-zero.")
    return sp.simplify((v1.dot(v2) / denominator) * v2)


def vector_rejection(v1, v2):
    v1 = _as_vector(v1)
    return sp.simplify(v1 - projection(v1, v2))


def is_parallel(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    if sp.simplify(v1.dot(v1)) == 0 or sp.simplify(v2.dot(v2)) == 0:
        return False
    return sp.Matrix.hstack(v1, v2).rank() == 1


def is_perpendicular(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    return sp.simplify(v1.dot(v2)) == 0


def scalar_triple_product(v1, v2, v3):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    v3 = _as_vector(v3)
    if not (v1.rows == v2.rows == v3.rows == 3):
        raise ValueError("Scalar triple product requires three 3D vectors.")
    return sp.simplify(v1.dot(v2.cross(v3)))


def vector_triple_product(v1, v2, v3):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    v3 = _as_vector(v3)
    if not (v1.rows == v2.rows == v3.rows == 3):
        raise ValueError("Vector triple product requires three 3D vectors.")
    return sp.simplify(v1.cross(v2.cross(v3)))


def parallelogram_area(v1, v2):
    v1 = _as_vector(v1)
    v2 = _as_vector(v2)
    _require_same_dimension(v1, v2)
    if v1.rows == 2:
        return sp.Abs(v1[0] * v2[1] - v1[1] * v2[0])
    if v1.rows == 3:
        return sp.simplify(v1.cross(v2).norm())
    raise ValueError("Area from two vectors is supported for 2D or 3D vectors.")


def triangle_area(v1, v2):
    return sp.simplify(parallelogram_area(v1, v2) / 2)


def parallelepiped_volume(v1, v2, v3):
    return sp.Abs(scalar_triple_product(v1, v2, v3))


def are_coplanar(v1, v2, v3):
    return sp.simplify(scalar_triple_product(v1, v2, v3)) == 0


def vector_line(point, direction, parameter=None):
    point = _as_vector(point)
    direction = _as_vector(direction)
    _require_same_dimension(point, direction)
    _require_nonzero(direction, "direction vector")
    if point.rows not in {2, 3}:
        raise ValueError("Vector line form is supported for 2D or 3D.")

    t = parameter or sp.Symbol("t")
    coordinate_symbols = sp.symbols("x y z")[: point.rows]
    return sp.Tuple(*(
        sp.Eq(symbol, sp.simplify(point[index] + t * direction[index]), evaluate=False)
        for index, symbol in enumerate(coordinate_symbols)
    ))


def plane_from_point_normal(point, normal):
    point = _as_vector(point)
    normal = _as_vector(normal)
    if point.rows != 3 or normal.rows != 3:
        raise ValueError("Plane equations require a 3D point and a 3D normal vector.")
    _require_nonzero(normal, "normal vector")
    x, y, z = sp.symbols("x y z")
    expression = normal.dot(Vector([x - point[0], y - point[1], z - point[2]]))
    return sp.Eq(sp.expand(expression), 0, evaluate=False)


SYMPY_LOCALS = {
    "Vector": Vector,
    "magnitude": magnitude,
    "unit_vector": unit_vector,
    "angle_between": angle_between,
    "scalar_projection": scalar_projection,
    "projection": projection,
    "vector_rejection": vector_rejection,
    "is_parallel": is_parallel,
    "is_perpendicular": is_perpendicular,
    "scalar_triple_product": scalar_triple_product,
    "vector_triple_product": vector_triple_product,
    "parallelogram_area": parallelogram_area,
    "triangle_area": triangle_area,
    "parallelepiped_volume": parallelepiped_volume,
    "are_coplanar": are_coplanar,
    "vector_line": vector_line,
    "plane_from_point_normal": plane_from_point_normal,
}

RULES = [
    "For VECTOR OPS: Use Vector([x, y, z]) syntax. Use .cross() for cross product, .dot() for dot product, .magnitude() or magnitude(v) for magnitude.",
    "For VECTOR ADDITION: Use Vector([x1, y1, z1]) + Vector([x2, y2, z2]).",
    "For UNIT VECTOR: Use unit_vector(Vector([...])) or Vector([...]).normalize().",
    "For ANGLE BETWEEN VECTORS: Use angle_between(v1, v2).",
    "For VECTOR PROJECTION: Use projection(v1, v2) for projection of v1 onto v2; use scalar_projection(v1, v2) for scalar projection.",
    "For PARALLEL/PERPENDICULAR CHECKS: Use is_parallel(v1, v2) or is_perpendicular(v1, v2).",
    "For TRIPLE PRODUCTS: Use scalar_triple_product(v1, v2, v3) or vector_triple_product(v1, v2, v3).",
    "For AREA/VOLUME: Use parallelogram_area(v1, v2), triangle_area(v1, v2), or parallelepiped_volume(v1, v2, v3).",
    "For VECTOR LINE/PLANE EQUATIONS: Use vector_line(point_vector, direction_vector) or plane_from_point_normal(point_vector, normal_vector).",
]

EXAMPLES = [
    'User problem: Cross product of <1,2,3> and <4,5,6>\nJSON: {"operation":"evaluate","expression":"Vector([1, 2, 3]).cross(Vector([4, 5, 6]))"}',
    'User problem: Dot product of <1,2> and <3,4>\nJSON: {"operation":"evaluate","expression":"Vector([1, 2]).dot(Vector([3, 4]))"}',
    'User problem: Unit vector of <3,4>\nJSON: {"operation":"evaluate","expression":"Vector([3, 4]).normalize()"}',
    'User problem: angle between <1,0> and <0,1>\nJSON: {"operation":"evaluate","expression":"angle_between(Vector([1, 0]), Vector([0, 1]))"}',
    'User problem: projection of <3,4> onto <1,0>\nJSON: {"operation":"evaluate","expression":"projection(Vector([3, 4]), Vector([1, 0]))"}',
    'User problem: scalar projection of <3,4> onto <1,0>\nJSON: {"operation":"evaluate","expression":"scalar_projection(Vector([3, 4]), Vector([1, 0]))"}',
    'User problem: are <2,4> and <1,2> parallel\nJSON: {"operation":"evaluate","expression":"is_parallel(Vector([2, 4]), Vector([1, 2]))"}',
    'User problem: are <1,2> and <2,-1> perpendicular\nJSON: {"operation":"evaluate","expression":"is_perpendicular(Vector([1, 2]), Vector([2, -1]))"}',
    'User problem: scalar triple product of <1,2,3>, <4,5,6>, <7,8,9>\nJSON: {"operation":"evaluate","expression":"scalar_triple_product(Vector([1, 2, 3]), Vector([4, 5, 6]), Vector([7, 8, 9]))"}',
    'User problem: area of triangle formed by <1,0,0> and <0,1,0>\nJSON: {"operation":"evaluate","expression":"triangle_area(Vector([1, 0, 0]), Vector([0, 1, 0]))"}',
    'User problem: line through (1,2,3) in direction <4,5,6>\nJSON: {"operation":"evaluate","expression":"vector_line(Vector([1, 2, 3]), Vector([4, 5, 6]))"}',
    'User problem: plane through (1,2,3) with normal <4,5,6>\nJSON: {"operation":"evaluate","expression":"plane_from_point_normal(Vector([1, 2, 3]), Vector([4, 5, 6]))"}',
]


VECTOR_MARKERS = (
    "Vector(",
    "magnitude(",
    "unit_vector(",
    "angle_between(",
    "scalar_projection(",
    "projection(",
    "vector_rejection(",
    "is_parallel(",
    "is_perpendicular(",
    "scalar_triple_product(",
    "vector_triple_product(",
    "parallelogram_area(",
    "triangle_area(",
    "parallelepiped_volume(",
    "are_coplanar(",
    "vector_line(",
    "plane_from_point_normal(",
)


def is_vector_expression(expr_text: str) -> bool:
    return any(marker in expr_text for marker in VECTOR_MARKERS)


def execute(task: MathTask, expr, variables: list, equations: list):
    expr_text = task.expression or task.equation or ""
    if task.operation == "evaluate" and is_vector_expression(expr_text):
        if isinstance(expr, (bool, tuple)):
            return expr
        if isinstance(expr, sp.MatrixBase):
            return expr
        try:
            return sp.simplify(expr)
        except Exception:
            return expr
    return None


def get_steps(task: MathTask, expr_str: str, result: Any):
    if not is_vector_expression(expr_str):
        return None

    if "angle_between(" in expr_str or ".angle_with(" in expr_str:
        lines = [
            "1. Identify the two vectors.",
            "2. Use cos(θ) = (A·B) / (|A||B|).",
            "3. Solve for θ using arccos.",
            "4. The angle is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "magnitude(" in expr_str or ".magnitude()" in expr_str:
        lines = [
            "1. Identify the vector components.",
            "2. Apply the magnitude formula: |v| = √(x² + y² + z²).",
            "3. The vector magnitude is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "unit_vector(" in expr_str or ".normalize()" in expr_str:
        lines = [
            "1. Calculate the magnitude of the vector.",
            "2. Divide each component by the magnitude.",
            "3. The unit vector is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "scalar_projection(" in expr_str or ".scalar_projection_onto(" in expr_str:
        lines = [
            "1. Identify the vector and the projection direction.",
            "2. Use scalar projection comp_b(a) = (a·b) / |b|.",
            "3. The scalar projection is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "projection(" in expr_str or ".projection_onto(" in expr_str:
        lines = [
            "1. Identify the vector being projected and the direction vector.",
            "2. Use proj_b(a) = (a·b / b·b)b.",
            "3. The projection vector is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "vector_rejection(" in expr_str:
        lines = [
            "1. Find the projection of the vector onto the direction vector.",
            "2. Subtract the projection from the original vector.",
            "3. The rejection component is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "is_parallel(" in expr_str:
        lines = [
            "1. Compare whether one vector is a scalar multiple of the other.",
            "2. Equivalently, check that the two-column matrix has rank 1.",
            "3. Parallel check result:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "is_perpendicular(" in expr_str:
        lines = [
            "1. Compute the dot product of the two vectors.",
            "2. If A·B = 0, the vectors are perpendicular.",
            "3. Perpendicular check result:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "scalar_triple_product(" in expr_str:
        lines = [
            "1. Compute B × C.",
            "2. Dot the result with A.",
            "3. The scalar triple product is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "vector_triple_product(" in expr_str:
        lines = [
            "1. Compute the inner cross product B × C.",
            "2. Cross A with that result.",
            "3. The vector triple product is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "parallelogram_area(" in expr_str or "triangle_area(" in expr_str:
        lines = [
            "1. Use the magnitude of the cross product for area.",
            "2. For a triangle, take half of the parallelogram area.",
            "3. The area is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "parallelepiped_volume(" in expr_str:
        lines = [
            "1. Use the absolute value of the scalar triple product.",
            "2. This gives the volume of the parallelepiped.",
            "3. The volume is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "are_coplanar(" in expr_str:
        lines = [
            "1. Compute the scalar triple product.",
            "2. If it equals 0, the three vectors are coplanar.",
            "3. Coplanarity check result:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "vector_line(" in expr_str:
        lines = [
            "1. Use the vector line form r = r₀ + t·d.",
            "2. Convert each component into a parametric equation.",
            "3. The line equations are:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if "plane_from_point_normal(" in expr_str:
        lines = [
            "1. Use the plane form n·(r - r₀) = 0.",
            "2. Substitute the point and normal vector.",
            "3. The plane equation is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if ".cross(" in expr_str:
        lines = [
            "1. Identify the two vectors for cross product.",
            "2. Set up the determinant of a 3x3 matrix:",
            "   |  i   j   k  |",
            "   | v1x v1y v1z |",
            "   | v2x v2y v2z |",
            "3. The cross product result is orthogonal to both input vectors.",
            "4. Final Result:",
            indented_math(result),
        ]
        return "\n".join(lines)

    if ".dot(" in expr_str:
        lines = [
            "1. Identify the two vectors for dot product.",
            "2. Apply the formula: A·B = |A||B|cos(θ)",
            "3. For component form: A·B = A_x*B_x + A_y*B_y + A_z*B_z",
            "4. The scalar result is:",
            indented_math(result),
        ]
        return "\n".join(lines)

    lines = [
        "1. Identify the vector operation from the expression.",
        "2. Apply component-wise vector algebra.",
        "3. The vector result is:",
        indented_math(result),
    ]
    return "\n".join(lines)
