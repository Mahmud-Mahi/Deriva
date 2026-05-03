import argparse
import itertools
import json
import re
import sys
import termios
import threading
import time
import tty
import urllib.error
import urllib.request
from contextlib import contextmanager
from typing import Any

import sympy as sp
from sympy.parsing.sympy_parser import convert_xor, implicit_multiplication_application, parse_expr, standard_transformations

from models import MathTask
from formatter import indented_math, pretty_math, add_step_breaks
from modules import get_all_locals, get_all_rules, get_all_examples, execute_task, get_solution_steps

try:
    import readline
except ImportError:
    readline = None

DEFAULT_MODEL = "qwen2-math:7b"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"

APP_NAME = "Deriva"
APP_SLOGAN = "Beneath the symbols"
ANSI_RESET = "\033[0m"
ANSI_BOLD_CYAN = "\033[1;96m"
ANSI_BOLD_LIGHT_GREY = "\033[1;37m"
ANSI_LIGHT_GREY = "\033[37m"
ANSI_DIM_WHITE = "\033[2;37m"
HIDE_CURSOR = "\033[?25l"
SHOW_CURSOR = "\033[?25h"
INPUT_PROMPT = "∂>  "
INPUT_PLACEHOLDER = "Let's unfold the math"
INPUT_HISTORY: list[str] = []

TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)
THINKING_FRAMES = ("thinking.", "thinking..", "thinking...")
THINKING_FRAME_SECONDS = 0.18

SYMPY_LOCALS = get_all_locals()

def ask_ollama(prompt: str, model: str, ollama_url: str, temperature: float = 0.0, json_mode: bool = False) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": temperature}}
    if json_mode: payload["format"] = "json"
    request = urllib.request.Request(ollama_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8")).get("response", "").strip()
    except Exception as exc:
        raise RuntimeError(f"Ollama Error: Start Ollama and run `ollama pull {model}`.") from exc

@contextmanager
def thinking_indicator(enabled: bool = True):
    if not enabled: yield; return
    done = threading.Event()
    def animate():
        for frame in itertools.cycle(THINKING_FRAMES):
            if done.is_set(): break
            print(f"\r{frame.ljust(15)}", end="", flush=True); time.sleep(THINKING_FRAME_SECONDS)
    thread = threading.Thread(target=animate, daemon=True)
    print(HIDE_CURSOR, end="", flush=True)
    thread.start()
    try: yield
    finally:
        done.set(); thread.join()
        print("\r" + " " * 15 + "\r" + SHOW_CURSOR, end="", flush=True)

def colorize(text: str, color: str, enabled: bool = True) -> str:
    return f"{color}{text}{ANSI_RESET}" if enabled else text

def print_logo(use_color: bool = True) -> None:
    logo_lines = [
        " ____  _____ ____  _____     ___     ",
        "|  _ \\| ____|  _ \\|_ _\\ \\   / / \\    ",
        "| | | |  _| | |_) || | \\ \\ / / _ \\   ",
        "| |_| | |___|  _ < | |  \\ V / ___ \\  ",
        "|____/|_____|_| \\_\\___|  \\_/_/   \\_\\ ",
    ]
    width = max(len(line) for line in logo_lines)
    print()
    for line in logo_lines: print(colorize(line, ANSI_BOLD_CYAN, use_color))
    print(colorize(APP_SLOGAN.center(width), ANSI_BOLD_LIGHT_GREY, use_color))
    print()

def parse_math(text: str) -> sp.Basic:
    cleaned = text.strip()
    if "=" in cleaned and not cleaned.startswith("Eq(") and not any(op in cleaned for op in ("<=", ">=", "!=", "==")):
        left, right = cleaned.split("=", 1)
        cleaned = f"Eq({left.strip()}, {right.strip()})"
    return parse_expr(cleaned, local_dict=SYMPY_LOCALS, global_dict={}, transformations=TRANSFORMATIONS, evaluate=True)

# RESTORED: Your custom bypass parser
def infer_task_from_problem(problem: str) -> MathTask | None:
    cleaned = problem.strip()
    lower = cleaned.lower()
    compact = re.sub(r"\s+", "", lower)

    if "circle" in lower and ("touch" in lower or "tangent" in lower) and "x=0" in compact and "y=0" in compact and "x=a" in compact:
        return MathTask(operation="circle_tangent_coordinate_lines", variables=["x", "y"])

    if lower.startswith("solve ") and "=" in cleaned:
        equation = cleaned[6:].strip()
        variable_match = re.search(r"[A-Za-z_][A-Za-z0-9_]*", equation)
        variable = variable_match.group(0) if variable_match else "x"
        if not equation.startswith("Eq("):
            left, right = equation.split("=", 1)
            equation = f"Eq({left.strip()}, {right.strip()})"
        return MathTask(operation="solve", equation=equation, variable=variable)
    return None

# RESTORED: Your custom parser fixer
def repair_common_parse_errors(problem: str, task: MathTask) -> MathTask:
    problem_lower = problem.lower()
    if ("sqrt" in problem_lower or "√" in problem) and not ("square" in problem_lower or "squared" in problem_lower):
        if "sqrt(" in task.expression:
            task.expression = re.sub(r"(sqrt\([^()]*\))\s*\*\*\s*2", r"\1", task.expression)
    return task

def make_task(problem: str, model: str, ollama_url: str) -> MathTask:
    inferred = infer_task_from_problem(problem)
    if inferred: return inferred

    rules = "\n".join(f"- {rule}" for rule in get_all_rules())
    examples = "\n\n".join(get_all_examples())
    
    prompt = f"""You are the parser in this architecture: User Input -> Qwen2-Math -> Parse -> SymPy -> Final Answer. Convert the user's math problem into exactly one JSON object for SymPy.
Return JSON only. Do not solve the problem in prose.
Allowed operations: solve|solve_ode|simplify|factor|expand|differentiate|integrate|limit|evaluate
JSON schema: {{"operation": "...", "expression": "...", "equation": "...", "equations": [], "variable": "x", "variables": ["x", "y"], "lower_bound": "", "upper_bound": "", "point": "", "direction": "+-"}}
Rules:
{rules}
Examples:
{examples}

User problem: {problem}"""

    raw = ask_ollama(prompt, model=model, ollama_url=ollama_url, json_mode=True)
    match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
    data = json.loads(match.group(0)) if match else {}
    
    task = MathTask(
        operation=str(data.get("operation", "evaluate")).lower().strip(),
        expression=str(data.get("expression", "") or ""),
        equation=str(data.get("equation", "") or ""),
        equations=data.get("equations") if isinstance(data.get("equations"), list) else None,
        variable=str(data.get("variable", "x") or "x"),
        variables=data.get("variables") if isinstance(data.get("variables"), list) else None,
        lower_bound=str(data.get("lower_bound", "") or ""),
        upper_bound=str(data.get("upper_bound", "") or ""),
        point=str(data.get("point", "") or ""),
        direction=str(data.get("direction", "+-") or "+-")
    )
    return repair_common_parse_errors(problem, task)

def solve_with_sympy(task: MathTask) -> Any:
    variable = sp.Symbol(task.variable) if task.variable else sp.Symbol("x")
    variables = [sp.Symbol(v) for v in (task.variables or [task.variable])]
    
    raw_items = task.equations or ([task.equation] if task.equation else [task.expression])
    equations = [parse_math(item) for item in raw_items if item]
    expr = equations[0] if equations else None

    res = execute_task(task, expr, variables, equations)
    if res is not None: return res
    
    if task.operation == "evaluate" and expr:
        try: return sp.N(expr) if expr.free_symbols else sp.simplify(expr)
        except AttributeError: return expr

    raise ValueError(f"Unsupported operation logic: {task.operation!r}")

def solution_steps(task: MathTask, result: Any) -> str:
    expr_str = task.expression or task.equation
    module_steps = get_solution_steps(task, expr_str, result)
    if module_steps: return add_step_breaks(module_steps)
    
    lines = [f"1. Apply SymPy operation: {task.operation}.", "2. The result is:", indented_math(result)]
    return add_step_breaks("\n".join(lines))

def final_answer(task: MathTask, result: Any) -> str:
    exact = pretty_math(result)
    lines = ["Answer:", indented_math(result)]
    try:
        if getattr(result, "free_symbols", set()) or getattr(result, "is_Matrix", False): raise ValueError
        decimal = sp.N(result, 12)
        if pretty_math(decimal) != exact: lines.extend(["Decimal:", indented_math(decimal)])
    except Exception: pass

    # RESTORED: Custom messaging for definite integrals
    if task.operation == "integrate" and task.lower_bound and task.upper_bound:
        lines.append(f"SymPy computed the definite integral from {task.lower_bound} to {task.upper_bound}.")
    else:
        lines.append(f"SymPy computed this using operation: {task.operation}.")
    return "\n".join(lines)

def run_once(problem: str, model: str, ollama_url: str, show_steps: bool = True, debug: bool = False):
    with thinking_indicator(sys.stdout.isatty()):
        task = make_task(problem, model, ollama_url)
        result = solve_with_sympy(task)
    if debug:
        print("\nParsed task:\n", json.dumps(task.__dict__, indent=2))
        print("\nSymPy result:\n", sp.sstr(result))
    if show_steps: print("\nSolution steps:\n", solution_steps(task, result))
    print("\nFinal answer:\n", final_answer(task, result), "\n")

def read_interactive_problem() -> str:
    prompt = colorize(INPUT_PROMPT, ANSI_BOLD_CYAN)
    placeholder = colorize(INPUT_PLACEHOLDER, ANSI_DIM_WHITE)
    show_first_prompt_hint = not INPUT_HISTORY
    buffer, cursor_position, history_index = [], 0, len(INPUT_HISTORY)
    old_settings, cursor_visible = termios.tcgetattr(sys.stdin), True

    def set_buffer(text: str): nonlocal cursor_position; buffer.clear(); buffer.extend(text); cursor_position = len(buffer)
    def set_cursor_visible(visible: bool): nonlocal cursor_visible; print(SHOW_CURSOR if visible else HIDE_CURSOR, end="", flush=True); cursor_visible = visible
    def render(show_placeholder: bool = False):
        text = "".join(buffer)
        hint = placeholder if show_placeholder and not text else ""
        set_cursor_visible(not hint)
        print(f"\r\033[K{prompt}{text}{hint}", end="", flush=True)
        if text and cursor_position < len(buffer): print(f"\033[{len(buffer) - cursor_position}D", end="", flush=True)
    def move_history(direction: int):
        nonlocal history_index
        if not INPUT_HISTORY: return
        history_index = max(0, min(len(INPUT_HISTORY), history_index + direction))
        if history_index == len(INPUT_HISTORY): set_buffer(""); render(show_placeholder=show_first_prompt_hint); return
        set_buffer(INPUT_HISTORY[history_index]); render()

    try:
        tty.setraw(sys.stdin.fileno())
        render(show_placeholder=show_first_prompt_hint)
        while True:
            char = sys.stdin.read(1)
            if char in {"\r", "\n"}:
                print()
                problem = "".join(buffer).strip()
                if problem and (not INPUT_HISTORY or INPUT_HISTORY[-1] != problem): INPUT_HISTORY.append(problem)
                return problem
            if char == "\x03": raise KeyboardInterrupt
            if char == "\x04":
                if not buffer: raise EOFError
                continue
            if char in {"\x7f", "\b"}:
                if cursor_position > 0: del buffer[cursor_position - 1]; cursor_position -= 1
                render(show_placeholder=show_first_prompt_hint and not buffer)
                continue
            if char == "\x1b":
                seq = sys.stdin.read(2)
                if seq == "[A": move_history(-1)
                elif seq == "[B": move_history(1)
                elif seq == "[C": cursor_position = min(len(buffer), cursor_position + 1); render()
                elif seq == "[D": cursor_position = max(0, cursor_position - 1); render()
                continue
            if char.isprintable():
                history_index = len(INPUT_HISTORY)
                buffer.insert(cursor_position, char)
                cursor_position += 1
                render()
    finally:
        set_cursor_visible(True)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

def setup_terminal_input():
    if readline is None: return
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind('"\\e[D": backward-char')
    readline.parse_and_bind('"\\e[C": forward-char')
    readline.parse_and_bind('"\\e[A": previous-history')
    readline.parse_and_bind('"\\e[B": next-history')

def main() -> None:
    parser = argparse.ArgumentParser(description="Deriva - Math Pipeline")
    parser.add_argument("prompt", nargs="*", help="Math prompt to solve.")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--answer-only", action="store_true")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()
    
    setup_terminal_input()
    
    if args.prompt:
        run_once(" ".join(args.prompt), args.model, args.ollama_url, not args.answer_only, args.debug)
        return

    print_logo(sys.stdout.isatty())
    print(f"Model: {args.model}\nType 'quit' or 'exit' or press Ctrl+C to exit.\n")

    while True:
        try: problem = read_interactive_problem()
        except (KeyboardInterrupt, EOFError): break
        if problem.lower() in {"q", "quit", "exit"}: break
        if not problem: continue
        try: run_once(problem, args.model, args.ollama_url, not args.answer_only, args.debug)
        except Exception as exc: print(f"\nError: {exc}\n")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: print("\nGoodbye."); sys.exit(0)