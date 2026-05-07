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
    get_solution_steps,
    parse_topic_prefix,
    execute_topic_task,
    get_module_for_topic
)
from embeddings import get_embedding_engine, detect_topic_by_embedding
from help_system import print_brief_help, print_full_help

try:
    import readline
except ImportError:
    readline = None

# Initialize embedding engine (None if nomic-embed-text unavailable)
EMBEDDING_ENGINE = None

# --- CONSTANTS ---
APP_NAME = "Deriva"
APP_SLOGAN = "B E Y O N D   E Q U A T I O N S"
ANSI_RESET = "\033[0m"
ANSI_BOLD_CYAN = "\033[1;96m"
ANSI_BOLD_LIGHT_GREY = "\033[1;37m"
ANSI_DIM_WHITE = "\033[2;37m"
ANSI_BOLD_RED = "\033[1;31m"
ANSI_BOLD_GREEN = "\033[1;32m"
INPUT_PROMPT = "∂>  "

DEFAULT_MODEL = "qwen2-math:7b"
DEFAULT_OLLAMA_URL = "http://localhost:11434/api/generate"

# Enforce structured JSON output from Ollama so we reliably produce a MathTask.
MATH_TASK_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["operation"],
    "properties": {
        "operation": {"type": "string"},
        "expression": {"type": "string"},
        "equation": {"type": "string"},
        "equations": {"type": "array", "items": {"type": "string"}},
        "variable": {"type": "string"},
        "variables": {"type": "array", "items": {"type": "string"}},
        "lower_bound": {"type": "string"},
        "upper_bound": {"type": "string"},
        "point": {"type": "string"},
        "direction": {"type": "string"},
    },
}

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

def ask_ollama(prompt: str, model: str, url: str, format_value: Any | None = None) -> str:
    # Keep generation bounded; Deriva just needs a small JSON task description.
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 128,
        },
    }
    if format_value is not None:
        payload["format"] = format_value

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            resp_data = json.loads(response.read().decode("utf-8"))
            return resp_data.get("response", "").strip()
    except Exception as e:
        raise RuntimeError(f"Ollama connection error: {e}")

def make_task(problem: str, model: str, url: str) -> MathTask:
    rules = "\n".join(f"- {rule}" for rule in get_all_rules())
    examples = "\n\n".join(get_all_examples())
    prompt = f"Convert to SymPy JSON:\nRules:\n{rules}\nExamples:\n{examples}\nProblem: {problem}"

    last_error: Exception | None = None
    for attempt in range(3):
        # Ollama structured output can vary by version; use the supported "json" string mode.
        raw = ask_ollama(prompt, model, url, format_value="json")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            # Try to recover: extract the first {...} block from the response
            last_error = e
            start = raw.find("{")
            end = raw.rfind("}")
            if start != -1 and end != -1 and end > start:
                candidate = raw[start : end + 1]
                try:
                    data = json.loads(candidate)
                except Exception as e2:
                    last_error = e2
                    data = None
            else:
                data = None

        if isinstance(data, dict) and "operation" in data:
            return MathTask(**data)

        last_error = last_error or RuntimeError("missing operation in returned task JSON")

        # Nudge the model more aggressively on retry
        prompt = (
            "Return ONLY valid JSON for the MathTask. No markdown, no extra text.\n"
            f"Problem: {problem}\n"
            f"Rules:\n{rules}\n"
            f"Examples:\n{examples}\n"
        )

    raise RuntimeError(f"Failed to get valid task JSON from Ollama: {last_error}")

# --- MATH EXECUTION ---

def solve_with_sympy(task: MathTask) -> Any:
    locals_dict = get_all_locals()
    
    # 1. Parse main expression/equation
    expr = parse_math(task.expression or task.equation or "0", locals_dict)
    if isinstance(expr, list) and len(expr) > 0:
        expr = expr[0]
        
    # 2. Parse equations list safely
    raw_eqs = task.equations or ([task.equation] if task.equation else [])
    equations = []
    for e in raw_eqs:
        parsed_e = parse_math(e, locals_dict)
        if isinstance(parsed_e, list) and len(parsed_e) > 0:
            parsed_e = parsed_e[0]
        equations.append(parsed_e)

    # 3. Determine variables. If defaulting to 'x' but 'x' is missing, pick from free symbols.
    provided_vars = task.variables or ([task.variable] if task.variable else [])
    all_free_symbols = set(getattr(expr, "free_symbols", set()))
    for eq in equations:
        all_free_symbols.update(getattr(eq, "free_symbols", set()))

    if not provided_vars or (len(provided_vars) == 1 and provided_vars[0] == 'x' and sp.Symbol('x') not in all_free_symbols):
        if all_free_symbols:
            variables = sorted(list(all_free_symbols), key=lambda s: s.name)
            # Sync back to task for consistent UI steps
            task.variables = [v.name for v in variables]
            task.variable = variables[0].name
        else:
            variables = [sp.Symbol('x')]
    else:
        variables = [sp.Symbol(v) for v in provided_vars]

    # 4. Priority 1: Module-specific execution logic
    result = execute_task(task, expr, variables, equations)
    if result is not None: return result
    
    # 5. Fallback logic
    if task.operation == "solve":
        return sp.solve(equations or [expr], variables, dict=len(variables) > 1)
    return sp.simplify(expr)

# --- UI LOGIC ---

def colorize(text: str, color: str) -> str:
    return f"{color}{text}{ANSI_RESET}"


def bold_colorize(text: str, color: str) -> str:
    """Bold and colorize text."""
    return f"{ANSI_BOLD_CYAN}{color}{ANSI_RESET}{colorize(text, color)}"

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

def get_input() -> tuple[str, str | None]:
    """
    Get user input and parse for topic prefix.
    First checks for explicit prefix (e.g., /vector), then uses embeddings for semantic detection.
    Returns (cleaned_input, topic) where topic is None if no prefix/detection found.
    """
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
    raw_input = "\n".join(lines).strip()

    # 1. First check for explicit topic prefix (e.g., /vector, #algebra)
    topic, cleaned_input = parse_topic_prefix(raw_input)
    
    # 2. If no explicit prefix and embeddings available, try semantic detection
    if topic is None and EMBEDDING_ENGINE is not None:
        result = detect_topic_by_embedding(cleaned_input, EMBEDDING_ENGINE, threshold=0.55)
        if result:
            topic, confidence = result
            # Show auto-detected topic with confidence
            confidence_pct = int(confidence * 100)
            detection_msg = colorize(f"[auto-detected: /{topic} ({confidence_pct}% confidence)]", ANSI_DIM_WHITE)
            print(f"{detection_msg}")
    
    return cleaned_input, topic

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

def exit_on_no_connection():
    """Exit the application with an error message if internet connection is lost."""
    print(f"\n{ANSI_BOLD_RED}Connection Lost:{ANSI_RESET} Unable to reach Ollama server.")
    print("Please check your internet connection and ensure Ollama is running.\n")
    sys.exit(1)

def run_pipeline(problem: str, model: str, url: str, debug: bool, topic: str | None = None):
    # Check for internet connectivity before proceeding
    if not check_ollama(url):
        exit_on_no_connection()

    try:
        if topic:
            # Display the bold topic prefix
            topic_display = colorize(f"/{topic}", ANSI_BOLD_CYAN)
            print(f"\n{ANSI_BOLD_CYAN}Topic:{ANSI_RESET} {topic_display}\n")

            # Use module-specific execution
            with thinking_indicator():
                task, expr, variables, equations, result, module = execute_topic_task(
                    topic, problem, model, url
                )
        else:
            # Original LLM-based routing
            with thinking_indicator():
                task = make_task(problem, model, url)
                result = solve_with_sympy(task)

        if debug:
            print(f"\n{ANSI_DIM_WHITE}[DEBUG] Task: {task}{ANSI_RESET}")

        # Get solution steps (topic-specific if applicable)
        if topic:
            # Use module-specific steps
            steps = module.get_steps(task, task.expression or task.equation, result) if hasattr(module, "get_steps") else None
        else:
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
    global EMBEDDING_ENGINE
    
    parser = argparse.ArgumentParser(
        prog="deriva",
        description="Deriva — AI-Powered Symbolic Math Solver",
        add_help=False  # We'll handle help manually for custom formatting
    )
    parser.add_argument("prompt", nargs="*")
    parser.add_argument("-m", "--model", default=DEFAULT_MODEL)
    parser.add_argument("--ollama-url", default=DEFAULT_OLLAMA_URL)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("-h", "--help", action="store_true", help="Show brief help")
    parser.add_argument("--full-help", action="store_true", help="Show complete manual")
    
    args = parser.parse_args()
    
    # Handle help flags
    if args.help:
        print_brief_help()
        sys.exit(0)
    
    if args.full_help:
        print_full_help()
        sys.exit(0)

    setup_history()
    
    # Initialize embedding engine for semantic topic detection
    try:
        EMBEDDING_ENGINE = get_embedding_engine(args.ollama_url.replace("/api/generate", ""))
    except Exception:
        EMBEDDING_ENGINE = None

    if args.prompt:
        prompt_text = " ".join(args.prompt)
        # Parse for topic prefix in command line mode too
        topic, cleaned_prompt = parse_topic_prefix(prompt_text)
        run_pipeline(cleaned_prompt, args.model, args.ollama_url, args.debug, topic)
        return

    print_logo()
    
    # Ollama Running Check
    is_running = check_ollama(args.ollama_url)
    status_text = colorize("ONLINE", ANSI_BOLD_GREEN) if is_running else colorize("OFFLINE (Is Ollama running?)", ANSI_BOLD_RED)
    print(f"Ollama Status: {status_text}")
    print(f"Model: {colorize(args.model, ANSI_BOLD_CYAN)}")
    if EMBEDDING_ENGINE:
        embedding_status = colorize("enabled", ANSI_BOLD_GREEN)
        print(f"Semantic Detection: {embedding_status} (nomic-embed-text)")
    else:
        embedding_status = colorize("disabled", ANSI_DIM_WHITE)
        print(f"Semantic Detection: {embedding_status} (nomic-embed-text not available)")
    
    print(f"\n{ANSI_DIM_WHITE}--- Instructions ---")
    print(f"• Type 'exit' or 'quit' or press Ctrl+C to close.")
    print(f"• For MULTILINE input, end your line with a backslash (\\) and press Enter.")
    print(f"• Use /topic prefix for explicit topic selection (e.g., '/vector solve |v|=5').{ANSI_RESET}\n")

    while True:
        problem, topic = get_input()
        if not problem: continue
        if problem.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break

        # Pass the problem and topic to run_pipeline
        run_pipeline(problem, args.model, args.ollama_url, args.debug, topic)
        save_history()

if __name__ == "__main__":
    main()
