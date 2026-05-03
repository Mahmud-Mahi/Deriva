from dataclasses import dataclass

@dataclass
class MathTask:
    operation: str
    expression: str = ""
    equation: str = ""
    equations: list[str] | None = None
    variable: str = "x"
    variables: list[str] | None = None
    lower_bound: str = ""
    upper_bound: str = ""
    point: str = ""
    direction: str = "+-"