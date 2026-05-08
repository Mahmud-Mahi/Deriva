import argparse
import itertools
import json
import os
import re
import sys
import struct
import fcntl
import termios
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
from embeddings import get_embedding_engine, detect_topic_by_embedding, get_topic_prompt_enhancement
from help_system import print_brief_help, print_full_help, print_full_help_no_banner

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
    """Setup command history with proper readline configuration."""
    if not HISTORY_FILE_PATH.parent.exists():
        HISTORY_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    if readline:
        try:
            readline.read_history_file(HISTORY_FILE_PATH)
        except FileNotFoundError:
            pass
        
        try:
            # Configure readline for proper line editing behavior
            if hasattr(readline, 'parse_and_bind'):
                # Use emacs mode for better arrow key and backspace support
                readline.parse_and_bind('set editing-mode emacs')
                # Enable horizontal scrolling for long inputs to fix backspace issues
                readline.parse_and_bind('set horizontal-scroll-mode on')
                # Allow auto-mark of matched text from history
                readline.parse_and_bind('set mark-modified-lines on')
                
                # Word-wise navigation and editing
                readline.parse_and_bind(r'"\M-f": forward-word')
                readline.parse_and_bind(r'"\M-b": backward-word')
                readline.parse_and_bind(r'"\M-d": kill-word')
                readline.parse_and_bind(r'"\M-DEL": backward-kill-word')
                readline.parse_and_bind(r'"\C-w": backward-kill-word')
                
                # Case conversion
                readline.parse_and_bind(r'"\M-u": upcase-word')
                readline.parse_and_bind(r'"\M-l": downcase-word')
                
                # Backspace and delete - map both key codes to backward-delete-char
                readline.parse_and_bind(r'"\C-h": backward-delete-char')
                readline.parse_and_bind(r'"\C-?": backward-delete-char')
                readline.parse_and_bind(r'"DEL": backward-delete-char')
                
                # Additional bindings for reliability
                readline.parse_and_bind(r'"\177": backward-delete-char')  # Backspace ASCII code
                
                # Allow deleting characters and handling
                readline.parse_and_bind(r'"\C-d": delete-char')
                
                # Make sure history is searchable
                readline.parse_and_bind(r'"\C-r": reverse-search-history')
                readline.parse_and_bind(r'"\C-s": forward-search-history')
        except Exception:
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

def make_task(problem: str, model: str, url: str, topic: str | None = None) -> MathTask:
    rules = "\n".join(f"· {rule}" for rule in get_all_rules())
    examples = "\n\n".join(get_all_examples())
    
    # Get topic-specific enhancements if available
    topic_enhancement = get_topic_prompt_enhancement(topic) if topic else ""
    
    # First attempt: comprehensive prompt with full structure and topic awareness
    prompt = f"""### TASK: Convert Math Problem to SymPy JSON

**OUTPUT FORMAT (strict JSON):**
{{
  "operation": "solve|evaluate|simplify|factor|expand",
  "expression": "SymPy expression or empty string",
  "equation": "SymPy equation (lhs=rhs) or empty string",
  "equations": ["equ1", "equ2", ...] or empty array,
  "variable": "primary variable or empty string",
  "variables": ["var1", "var2"] or empty array
}}

**OPERATION TYPES:**
· solve: Solve equation(s) for variable(s). Use when problem asks "find", "solve", "determine", "what is x"
· evaluate: Evaluate/compute function/expression with constraints. Use for "evaluate", "compute", "apply", "find value"
· simplify: Simplify/reduce expression. Use for "simplify", "reduce", "show", "combine"
· factor: Factor polynomial/expression. Use for "factor", "factorize", "decompose"
· expand: Expand expression. Use for "expand", "distribute", "open brackets"

**CRITICAL RULES:**
{rules}

**REFERENCE EXAMPLES:**
{examples}

**PROBLEM TO SOLVE:**
{problem}{topic_enhancement}

**OUTPUT INSTRUCTIONS:**
1. Return ONLY valid JSON object (no markdown backticks, no explanations, no extra text)
2. "operation" field is REQUIRED - choose most appropriate type
3. Detect ALL variables from the problem and list in "variables"
4. For single variable x -> set both "variable": "x" AND "variables": ["x"]
5. Use SymPy syntax: ** for power, sqrt(), Eq(lhs, rhs) for equations
6. Multiple equations go in "equations" array, not "equation" field
7. If problem has bounds/constraints, include in expression/equation logic
8. Keep all expressions valid and concise
9. Empty fields use empty string "" for single values, empty array [] for lists"""

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

        last_error = last_error or RuntimeError("missing 'operation' field in returned task JSON")

        # Retry with stricter, more direct prompt
        if attempt == 1:
            prompt = f"""RESPOND WITH ONLY JSON - NO OTHER TEXT.

Format:
{{
  "operation": "solve|evaluate|simplify|factor|expand",
  "expression": "...",
  "equation": "...",
  "equations": [...],
  "variable": "...",
  "variables": [...]
}}

Problem: {problem}

Rules:
{rules}

Examples:
{examples}{topic_enhancement}

Return valid JSON object only:"""
        else:
            # Final retry: minimal but explicit prompt
            prompt = f"""Generate JSON only (valid JSON, nothing else):

Problem: {problem}

Respond with this format:
{{
  "operation": "solve",
  "expression": "",
  "equation": "",
  "equations": [],
  "variable": "x",
  "variables": ["x"]
}}

Adjust fields for the problem above. Return JSON only."""

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

def get_terminal_width() -> int:
    """Get terminal width, default to 80 if unable to determine."""
    try:
        size = struct.unpack('HHHW', fcntl.ioctl(sys.stdout, termios.TIOCSWINSZ, struct.pack('HHHW', 0, 0, 0, 0)))
        return size[1] if size[1] > 0 else 80
    except:
        return 80

def print_wrapped_input(text: str, prompt: str, cursor_pos: int) -> int:
    """
    Print text with wrapping and return number of lines used.
    Handles proper display of multi-line input on terminal.
    """
    prompt_len = len(prompt)
    terminal_width = get_terminal_width()
    available_width = terminal_width - prompt_len
    
    if available_width < 20:  # Minimum usable width
        available_width = 20
    
    lines_used = 1
    current_col = prompt_len
    
    # Display prompt
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    # Display text with wrapping
    for char in text:
        if char == '\n':
            sys.stdout.write('\n')
            current_col = 0
            lines_used += 1
        else:
            if current_col >= available_width:
                sys.stdout.write('\n')
                current_col = 0
                lines_used += 1
            sys.stdout.write(char)
            current_col += 1
    
    sys.stdout.flush()
    return lines_used

def get_input() -> tuple[str, str | None]:
    """
    Get user input with proper long text support.
    Uses Python's built-in input() for terminal wrapping.
    Arrow keys, backspace, and history work automatically via readline.
    Press ESC or Ctrl+C to cancel input.
    """
    prompt = colorize(INPUT_PROMPT, ANSI_BOLD_CYAN)
    lines = []
    current_prompt = prompt
    
    while True:
        try:
            line = input(current_prompt)
            
            # If line ends with backslash, continue multi-line input
            if line.endswith('\\'):
                lines.append(line[:-1])  # Remove the backslash
                current_prompt = colorize(" >  ", ANSI_BOLD_CYAN)
            else:
                lines.append(line)
                break
                
        except EOFError:
            print("\nGoodbye.")
            sys.exit(0)
        except KeyboardInterrupt:
            # Ctrl+C cancels input - return empty
            print()
            return "", None
    
    raw_input = "\n".join(lines).strip()
    
    if not raw_input:
        return "", None
    
    # Parse topic prefix
    topic, cleaned_input = parse_topic_prefix(raw_input)
    
    # Skip semantic detection for special commands
    special_commands = {"help", "/help", "exit", "quit"}
    is_special_command = cleaned_input.lower() in special_commands
    
    # Semantic detection if available
    if topic is None and EMBEDDING_ENGINE is not None and not is_special_command:
        result = detect_topic_by_embedding(cleaned_input, EMBEDDING_ENGINE, threshold=0.55)
        if result:
            topic, confidence = result
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
            # Original LLM-based routing - let make_task handle semantic detection internally
            with thinking_indicator():
                task = make_task(problem, model, url, None)
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
    print(f"• Type 'exit' or 'quit' to close the application.")
    print(f"• Press ESC to cancel input and start over.")
    print(f"• Use arrow keys (↑↓) to navigate history, (←→) to move cursor.")
    print(f"• Use backspace or delete to remove characters.")
    print(f"• Type long questions (300+ words) - input wraps automatically.")
    print(f"• Press Ctrl+C to interrupt a running operation.")
    print(f"• Type '/help' for detailed documentation.")
    print(f"• Use /topic prefix for explicit topic selection (e.g., '/vector solve |v|=5').{ANSI_RESET}\n")

    while True:
        problem, topic = get_input()
        if not problem: continue
        if problem.lower() in {"exit", "quit"}:
            print("Goodbye.")
            break
        
        # Handle /help command
        if problem.lower() == "help" or problem.lower().startswith("/help"):
            print_full_help_no_banner()
            continue

        # Pass the problem and topic to run_pipeline
        try:
            run_pipeline(problem, args.model, args.ollama_url, args.debug, topic)
        except KeyboardInterrupt:
            print(f"\n{colorize('Operation cancelled by user.', ANSI_BOLD_RED)}")
            # The thinking_indicator context manager handles its own cleanup (stopping the thread)
            # if it's interrupted by the exception.

        save_history()

if __name__ == "__main__":
    main()
