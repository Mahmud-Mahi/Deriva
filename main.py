import argparse
import itertools
import json
import re
import sys
import os
import threading
import time
import urllib.error
import urllib.request
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import sympy as sp
from models import MathTask
from formatter import (
    indented_math, 
    pretty_math, 
    add_step_breaks,
    parse_math
)

from modules import (
    get_all_locals, 
    get_all_rules, 
    get_all_examples, 
    execute_task, 
    get_solution_steps
)

try:
    import readline
except ImportError:
    readline = None

# --- CONSTANTS ---
APP_NAME = "Deriva"
APP_SLOGAN = "P R E C I S I O N  I N  E V E R Y  S T E P"
ANSI_RESET = "\033[0m"
ANSI_BOLD_CYAN = "\033[1;96m"
ANSI_BOLD_LIGHT_GREY = "\033[1;37m"
ANSI_DIM_WHITE = "\033[2;37m"
ANSI_BOLD_RED = "\033[1;31m"
ANSI_BOLD_GREEN = "\033[1;32m"
INPUT_PROMPT = "∂>  "

DEFAULT_MODEL = "qwen2-math:7b"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"

# --- PERSISTENT HISTORY ---
HISTORY_FILE_PATH = Path.home() / ".cache/deriva_history"

def setup_history():
    if not HISTORY_FILE_PATH.parent.exists():
        HISTORY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if readline:
        try:
            readline.read_history_file(HISTORY_FILE_PATH)
        except FileNotFoundError:
            pass

def save_history():
    if readline:
        readline.set_history_length(1000)
        readline.write_history_file(HISTORY_FILE_PATH)

# --- LLM INTERACTION ---

def check_ollama(url: str) -> bool:
    """Checks if the Ollama server is running."""
    try:
        # Check the base URL (not the generate endpoint) for a faster response
        base_url = url.replace("/api/generate", "")
        urllib.request.urlopen(base_url, timeout=2)
        return True
    except:
        return False

def ask_ollama(prompt: str, model: str, url: str, json_mode: bool = False) -> str:
    payload = {"model": model, "prompt": prompt, "stream": False, "options": {"temperature": 0.0}}
    if json_mode: payload["format"] = "json"
    
    request = urllib.request.Request(
        url, 
        data=json.dumps(payload).encode("utf-8"), 
        headers={"Content-Type": "application/json"}, 
        method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"Ollama connection error: {e}")

def make_task(problem: str, model: str, url: str) -> MathTask:
    rules = "\n".join(f"- {rule}" for rule in get_all_rules())
    examples = "\n\n".join(get_all_examples())
    prompt = f"Convert to SymPy JSON:\nRules:\n{rules}\nExamples:\n{examples}\nProblem: {problem}"
    raw = ask_ollama(prompt, model, url, json_mode=True)
    data = json.loads(raw)
    return MathTask(**data)

# --- MATH EXECUTION ---

def solve_with_sympy(task: MathTask) -> Any:
    locals_dict = get_all_locals()
    expr = parse_math(task.expression or task.equation or "0", locals_dict)
    variables = [sp.Symbol(v) for v in (task.variables or [task.variable])]
    equations = [parse_math(e, locals_dict) for e in (task.equations or [task.equation]) if e]

    # If SymPy parsed brackets [...] into a list, extract the content
    if isinstance(expr, (list, tuple)) and len(expr) > 0:
        expr = expr[0]
    
    # Handle equations list safely
    raw_eqs = task.equations or ([task.equation] if task.equation else [])
    equations = []
    for e in raw_eqs:
        parsed_e = parse_math(e, locals_dict)
        if isinstance(parsed_e, (list, tuple)) and len(parsed_e) > 0:
            parsed_e = parsed_e[0]
        equations.append(parsed_e)

    # Priority 1: Module logic
    result = execute_task(task, expr, variables, equations)
    if result is not None: return result
    result = execute_task(task, expr, variables, equations)
    
    if task.operation == "solve":
        return sp.solve(equations or [expr], variables, dict=len(variables) > 1)
    return sp.simplify(expr)

# --- UI LOGIC ---

def colorize(text: str, color: str) -> str:
    return f"{color}{text}{ANSI_RESET}"

def print_logo() -> None:
    logo_lines = [
        " ____  _____ ____  _____     ___     ",
        "|  _ \\| ____|  _ \\|_ _\\ \\   / / \\    ",
        "| | | |  _| | |_) || | \\ \\ / / _ \\   ",
        "| |_| | |___|  _ < | |  \\ V / ___ \\  ",
        "|____/|_____|_| \\_\\___|  \\_/_/   \\_\\ ",
    ]
    width = max(len(line) for line in logo_lines)
    print()
    for line in logo_lines: 
        print(colorize(line, ANSI_BOLD_CYAN))
    print(colorize(APP_SLOGAN.center(width), ANSI_BOLD_LIGHT_GREY))
    print()

def get_input() -> str:
    lines = []
    prompt = colorize(INPUT_PROMPT, ANSI_BOLD_CYAN)
    while True:
        try:
            line = input(prompt)
            if line.endswith('\\'):
                lines.append(line[:-1])
                prompt = colorize(" >  ", ANSI_BOLD_CYAN)
            else:
                lines.append(line)
                break
        except EOFError:
            print("\nGoodbye.")
            sys.exit(0)
        except KeyboardInterrupt:
            print("\nGoodbye.")
            sys.exit(0)
    return "\n".join(lines).strip()

@contextmanager
def thinking_indicator():
    # Print a newline first so the thinking indicator starts on its own line
    # sys.stdout.write("\n")
    done = threading.Event()
    def animate():
        for frame in itertools.cycle(["thinking.", "thinking..", "thinking..."]):
            if done.is_set(): break
            sys.stdout.write(f"\r{ANSI_DIM_WHITE}{frame.ljust(12)}{ANSI_RESET}")
            sys.stdout.flush()
            time.sleep(0.4)
    t = threading.Thread(target=animate, daemon=True)
    t.start()
    try: yield
    finally:
        done.set(); t.join()
        sys.stdout.write("\r\033[K")
        sys.stdout.flush()

def run_pipeline(problem: str, model: str, url: str, debug: bool):
    try:
        with thinking_indicator():
            task = make_task(problem, model, url)
            result = solve_with_sympy(task)
        
        if debug: print(f"\n{ANSI_DIM_WHITE}[DEBUG] Task: {task}{ANSI_RESET}")

        steps = get_solution_steps(task, task.expression or task.equation, result)
        if steps:
            print(f"\n{ANSI_BOLD_LIGHT_GREY}Solution steps:{ANSI_RESET}")
            print(add_step_breaks(steps))
        
        print(f"\n{ANSI_BOLD_CYAN}Final Answer:{ANSI_RESET}")
        print(indented_math(result))
        print()
    except Exception as e:
        print(f"\n{ANSI_BOLD_CYAN}Error:{ANSI_RESET} {e}\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    setup_history()
    
    if args.prompt:
        run_pipeline(" ".join(args.prompt), args.model, args.ollama_url, args.debug)
        return

    print_logo()
    
    # Ollama Running Check
    is_running = check_ollama(args.ollama_url)
    status_text = colorize("ONLINE", ANSI_BOLD_GREEN) if is_running else colorize("OFFLINE (Is Ollama running?)", ANSI_BOLD_RED)
    print(f"Ollama Status: {status_text}")
    print(f"Model: {colorize(args.model, ANSI_BOLD_CYAN)}")
    
    print(f"\n{ANSI_DIM_WHITE}--- Instructions ---")
    print(f"• Type 'exit' or 'quit' or press Ctrl+C to close.")
    print(f"• For MULTILINE input, end your line with a backslash (\\) and press Enter.{ANSI_RESET}\n")

    while True:
        problem = get_input()
        if not problem: continue
        if problem.lower() in {"exit", "quit"}: 
            print("Goodbye.")
            break
        
        run_pipeline(problem, args.model, args.ollama_url, args.debug)
        save_history()

if __name__ == "__main__":
    main()