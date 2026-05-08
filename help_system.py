"""
Comprehensive help and manual system for Deriva.
Provides detailed documentation via --help and interactive commands.
"""

from typing import Optional
import textwrap
from pathlib import Path

# ANSI Color codes
ANSI_RESET = "\033[0m"
ANSI_BOLD_CYAN = "\033[1;96m"
ANSI_BOLD_GREEN = "\033[1;32m"
ANSI_BOLD_YELLOW = "\033[1;33m"
ANSI_BOLD_WHITE = "\033[1;37m"
ANSI_BOLD_LIGHT_GREY = "\033[1;37m"
ANSI_DIM_WHITE = "\033[2;37m"

def colorize(text: str, color: str) -> str:
    """Apply color to text."""
    return f"{color}{text}{ANSI_RESET}"


def print_help_banner():
    """Print the main help banner with Deriva logo."""
    logo_lines = [
        " ____  _____ ____  _____     ___     ",
        "|  _ \\| ____|  _ \\|_ _\\ \\   / / \\    ",
        "| | | |  _| | |_) || | \\ \\ / / _ \\   ",
        "| |_| | |___|  _ < | |  \\ V / ___ \\  ",
        "|____/|_____|_| \\_\\___|  \\_/_/   \\_\\ ",
    ]
    slogan = "B E Y O N D   E Q U A T I O N S"
    
    print()
    for line in logo_lines:
        print(colorize(line, ANSI_BOLD_CYAN))
    print(colorize(slogan.center(35), ANSI_BOLD_LIGHT_GREY))
    print()
    print(colorize("AI-Powered Symbolic Math Solver | Version 1.0 | Python 3.10+", ANSI_DIM_WHITE))
    print()


def print_quick_start():
    """Print quick start guide."""
    print(f"\n{colorize('🚀 QUICK START', ANSI_BOLD_GREEN)}\n")
    print("  1. Start interactive mode:")
    print(f"     {colorize('$ pyton main.py', ANSI_DIM_WHITE)}\n")
    print("  2. Solve a single problem:")
    print(f"     {colorize('$ python main.py \"solve x^2 - 4 = 0\"', ANSI_DIM_WHITE)}\n")
    print("  3. Use explicit topic routing:")
    print(f"     {colorize('$ python main.py \"/vector dot product of (1,2,3) and (4,5,6)\"', ANSI_DIM_WHITE)}\n")
    print("  4. Enable semantic auto-detection:")
    print(f"     {colorize('$ python main.py \"find the center of circle x^2 + y^2 - 4x = 0\"', ANSI_DIM_WHITE)}\n")


def print_command_line_options():
    """Print all command-line options."""
    print(f"\n{colorize('⚙️  COMMAND-LINE OPTIONS', ANSI_BOLD_GREEN)}\n")
    
    options = [
        ("PROMPT [PROMPT ...]", "Math problem to solve (optional for interactive mode)"),
        ("-m, --model MODEL", "LLM model to use\n  Default: qwen2-math:7b\n  Options: qwen2-math:7b, neural-chat, mistral, etc."),
        ("--ollama-url URL", "Ollama API endpoint\n  Default: http://localhost:11434/api/generate"),
        ("--debug", "Show detailed debug information and intermediate steps"),
        ("-h, --help", "Show this help message and exit"),
    ]
    
    for opt, desc in options:
        print(f"  {colorize(opt, ANSI_BOLD_CYAN)}")
        # Indent description
        for line in desc.split('\n'):
            print(f"    {line}")
        print()


def print_topic_routing():
    """Print available topics and routing options."""
    print(f"\n{colorize('📊 TOPIC ROUTING SYSTEM', ANSI_BOLD_GREEN)}\n")
    
    print("Deriva uses smart topic routing to apply specialized math modules.\n")
    
    print(f"{colorize('Explicit Topic Prefix:', ANSI_BOLD_YELLOW)} (guaranteed routing)")
    print("  Syntax: /TOPIC problem | #TOPIC problem | TOPIC: problem\n")
    
    topics = {
        "algebra": "Polynomial factoring, solving equations, expansion",
        "vector": "Dot/cross product, magnitude, vector operations",
        "circle": "Radius, tangent lines, chord properties",
        "line / straight-line": "Linear equations, slopes, intercepts",
        "conics": "Parabolas, ellipses, hyperbolas, eccentricity",
        "matrix": "Determinants, inverses, eigenvalues",
        "trigonometry / trig": "Sin/cos/tan, identities, angle solvers",
        "inverse-trigonometry": "arcsin, arccos, arctan functions",
        "calculus": "Derivatives, integrals, limits, differential equations",
        "combination / permutation": "nCr, nPr, arrangements",
        "geometry": "Area, perimeter, volume calculations",
    }
    
    for topic, desc in topics.items():
        print(f"  {colorize(f'/{topic:<25}', ANSI_BOLD_CYAN)} {desc}")
    
    print(f"\n{colorize('Semantic Auto-Detection:', ANSI_BOLD_YELLOW)} (when nomic-embed-text available)")
    print("  • No prefix needed — analyzes problem intent")
    print("  • Shows confidence score (%)")
    print("  • Example:")
    print(f"    {colorize('∂> Find tangent line to circle at (3,4)', ANSI_DIM_WHITE)}")
    print(f"    {colorize('[auto-detected: /circle (78% confidence)]', ANSI_DIM_WHITE)}\n")


def print_interactive_commands():
    """Print interactive mode commands."""
    print(f"\n{colorize('💻 INTERACTIVE MODE COMMANDS', ANSI_BOLD_GREEN)}\n")
    
    commands = [
        ("/help", "Show complete help and documentation"),
        ("help", "Show complete help (alias)"),
        ("exit", "Quit Deriva"),
        ("quit", "Quit Deriva"),
        ("?", "Show available topics"),
        ("/TOPIC problem", "Route to specific topic module"),
        ("#TOPIC problem", "Alternative topic prefix syntax"),
        ("TOPIC: problem", "Alternative topic prefix syntax"),
        ("\\", "Continue input on next line (multiline input)"),
    ]
    
    for cmd, desc in commands:
        print(f"  {colorize(f'{cmd:<30}', ANSI_BOLD_CYAN)} {desc}")
    print()


def print_usage_examples():
    """Print comprehensive usage examples."""
    print(f"\n{colorize('📚 USAGE EXAMPLES', ANSI_BOLD_GREEN)}\n")
    
    examples = [
        ("General Solving", "python main.py \"solve x^2 - 9 = 0\""),
        ("Algebra", "python main.py \"/algebra factor (x^2 - 4x + 4)\""),
        ("Vector Operations", "python main.py \"/vector dot product of (1,0,1) and (0,1,0)\""),
        ("Circle", "python main.py \"#circle find center of x^2 + y^2 - 6x + 4y = 3\""),
        ("Calculus", "python main.py \"calculus: derivative of x^3 + 2x^2\""),
        ("Trigonometry", "python main.py \"/trig solve sin(x) = 0.5\""),
        ("Matrix", "python main.py \"#matrix inverse of [[1,2],[3,4]]\""),
        ("Multiline (interactive)", "python main.py\n  ∂> x^2 + y^2 = 25\\\n     and x - y = 1"),
        ("With Custom Model", "python main.py -m neural-chat \"solve 3x + 5 = 20\""),
        ("Debug Mode", "python main.py --debug \"solve x^2 = 16\""),
    ]
    
    for title, cmd in examples:
        print(f"  {colorize(title, ANSI_BOLD_YELLOW)}")
        print(f"    {colorize('$', ANSI_DIM_WHITE)} {cmd}\n")


def print_troubleshooting():
    """Print troubleshooting guide."""
    print(f"\n{colorize('🔧 TROUBLESHOOTING', ANSI_BOLD_GREEN)}\n")
    
    issues = [
        ("Ollama connection error", [
            "1. Ensure Ollama is running: $ ollama serve",
            "2. Check URL: $ python main.py --ollama-url http://localhost:11434/api/generate",
            "3. Verify model is available: $ ollama list",
            "4. Pull default model: $ ollama pull qwen2-math:7b",
        ]),
        ("'Semantic Detection: disabled'", [
            "1. Pull embedding model: $ ollama pull nomic-embed-text",
            "2. Restart Deriva",
            "3. Use explicit /topic prefix as fallback",
        ]),
        ("Slow first query", [
            "• Normal for embeddings (computing vectors)",
            "• Subsequent queries use cache (~100ms)",
            "• Use explicit /topic prefix to skip embedding",
        ]),
        ("Incorrect topic detection", [
            "1. Use explicit prefix: /vector ...",
            "2. Check auto-detected confidence %",
            "3. Enable --debug for detailed info",
        ]),
        ("Model not responding", [
            "1. Increase Ollama timeout: OLLAMA_TIMEOUT=300s",
            "2. Try simpler problem first",
            "3. Check Ollama logs: $ ollama logs",
        ]),
        ("Parse errors", [
            "1. Check math syntax: use ^ for exponents, not **",
            "2. Escape special chars properly",
            "3. Use explicit notation: Eq(x^2, 9) for equations",
        ]),
    ]
    
    for issue, solutions in issues:
        print(f"  {colorize(issue, ANSI_BOLD_YELLOW)}")
        for solution in solutions:
            print(f"    {solution}")
        print()


def print_features():
    """Print feature overview."""
    print(f"\n{colorize('✨ FEATURES', ANSI_BOLD_GREEN)}\n")
    
    features = [
        ("Natural Language Input", "Describe math problems in plain English"),
        ("Symbolic Computation", "Solve equations, simplify expressions, handle complex systems"),
        ("Step-by-Step Solutions", "Get detailed solution process for learning"),
        ("Smart Topic Routing", "Auto-detect or explicitly specify math domain"),
        ("Beautiful Formatting", "Fractions, powers, matrices, special symbols"),
        ("Interactive CLI", "Multi-line input, command history, real-time indicator"),
        ("Semantic Understanding", "AI comprehends problem intent via embeddings"),
        ("Customizable Models", "Use any Ollama-compatible model"),
        ("Performance Caching", "Fast repeated queries via embedding cache"),
    ]
    
    for feature, desc in features:
        print(f"  {colorize('•', ANSI_BOLD_GREEN)} {colorize(feature, ANSI_BOLD_CYAN)}")
        print(f"    {desc}\n")


def print_requirements():
    """Print system requirements."""
    print(f"\n{colorize('📋 SYSTEM REQUIREMENTS', ANSI_BOLD_GREEN)}\n")
    
    reqs = [
        ("Python", "3.10 or higher"),
        ("SymPy", "Required for symbolic math"),
        ("NumPy", "For semantic embeddings (optional)"),
        ("Ollama", "Running locally at localhost:11434"),
        ("LLM Model", "Default: qwen2-math:7b (pull with: ollama pull qwen2-math:7b)"),
        ("Embedding Model", "Optional: nomic-embed-text (for auto-detection)"),
        ("Memory", "2GB+ recommended for model running"),
        ("Network", "Ollama must be accessible on localhost"),
    ]
    
    for req, desc in reqs:
        print(f"  {colorize(req, ANSI_BOLD_CYAN):<20} {desc}")
    print()


def print_configuration():
    """Print configuration guide."""
    print(f"\n{colorize('⚙️  CONFIGURATION', ANSI_BOLD_GREEN)}\n")
    
    print("Environment Variables:\n")
    env_vars = [
        ("OLLAMA_HOST", "Set custom Ollama address (default: localhost:11434)"),
        ("OLLAMA_TIMEOUT", "Request timeout in seconds (default: 120)"),
        ("OLLAMA_CUDA_VISIBLE_DEVICES", "GPU acceleration control"),
    ]
    
    for var, desc in env_vars:
        print(f"  {colorize(var, ANSI_BOLD_CYAN):<30} {desc}")
    
    print(f"\n\nConfiguration Files:\n")
    print(f"  {colorize('~/.cache/deriva_history', ANSI_BOLD_CYAN):<30} Command history (auto-managed)")
    print(f"  {colorize('embeddings.py', ANSI_BOLD_CYAN):<30} Semantic settings (threshold, descriptions)")
    print()


def print_tips_and_tricks():
    """Print tips and tricks."""
    print(f"\n{colorize('💡 TIPS & TRICKS', ANSI_BOLD_GREEN)}\n")
    
    tips = [
        ("Use explicit topics", "Faster execution, no embedding computation"),
        ("Enable --debug", "See MathTask JSON and detailed computation steps"),
        ("Batch similar problems", "Embeddings cached — 2nd query much faster"),
        ("Check confidence %", "Auto-detected topics show accuracy score"),
        ("Multiline input", "Use \\ at end of line to continue next line"),
        ("Save history", "Command history automatically saved in ~/.cache/deriva_history"),
        ("Custom models", "Switch models for specialized domains with -m flag"),
        ("Verify Ollama", "Run 'ollama list' to see available models"),
        ("Stack problems", "Chain derivations: solve result, then integrate, etc."),
        ("Use variables", "Define x, y, z in expressions for multi-var problems"),
    ]
    
    for i, tip in enumerate(tips, 1):
        print(f"  {colorize(f'{i:2}.', ANSI_BOLD_YELLOW)} {colorize(tip[0], ANSI_BOLD_CYAN):<30} {tip[1]}")
    print()


def print_advanced_usage():
    """Print advanced usage patterns."""
    print(f"\n{colorize('🚀 ADVANCED USAGE', ANSI_BOLD_GREEN)}\n")
    
    print(f"{colorize('Custom Models:', ANSI_BOLD_YELLOW)}")
    print("  • Any Ollama model works: neural-chat, mistral, dolphin-mixtral")
    print("  • Pull model: $ ollama pull neural-chat")
    print("  • Use: $ python main.py -m neural-chat \"your problem\"\n")
    
    print(f"{colorize('Semantic Embeddings:', ANSI_BOLD_YELLOW)}")
    print("  • nomic-embed-text enables auto-detection (pull separately)")
    print("  • 768-dimensional embeddings for semantic similarity")
    print("  • Threshold adjustable in embeddings.py (default: 0.55)\n")
    
    print(f"{colorize('Batch Processing:', ANSI_BOLD_YELLOW)}")
    print("  • Combine problems: /algebra {expr1} and {expr2}")
    print("  • Use pipes: echo \"solve x^2=4\" | python main.py\n")
    
    print(f"{colorize('Extend Modules:', ANSI_BOLD_YELLOW)}")
    print("  • Create new module in modules/")
    print("  • Define RULES, EXAMPLES, execute() function")
    print("  • Register in modules/__init__.py TOPIC_TO_MODULE\n")
    
    print(f"{colorize('Performance Tuning:', ANSI_BOLD_YELLOW)}")
    print("  • Enable GPU in Ollama: export OLLAMA_CUDA=1")
    print("  • Use lighter model for speed: mistral, neural-chat")
    print("  • Cache embeddings by running --debug first query\n")


def print_api_reference():
    """Print API reference for extension."""
    print(f"\n{colorize('📖 API REFERENCE', ANSI_BOLD_GREEN)}\n")
    
    print(f"{colorize('Core Classes:', ANSI_BOLD_YELLOW)}\n")
    print("  class MathTask:")
    print("    • operation: str (e.g., 'solve', 'simplify', 'derivative')")
    print("    • expression: str (main math expression)")
    print("    • equation: str (single equation)")
    print("    • equations: list[str] (multiple equations)")
    print("    • variables: list[str] (x, y, z, etc.)")
    print("    • bounds, point, direction (for specialized operations)\n")
    
    print(f"{colorize('Key Functions:', ANSI_BOLD_YELLOW)}\n")
    print("  • make_task(problem, model, url) → MathTask")
    print("  • solve_with_sympy(task) → solutions")
    print("  • execute_topic_task(topic, problem, model, url) → (task, result, steps)")
    print("  • detect_topic_by_embedding(problem, engine) → (topic, confidence)\n")
    
    print(f"{colorize('Module Interface:', ANSI_BOLD_YELLOW)}\n")
    print("  • RULES: list[str] — guidelines for LLM")
    print("  • EXAMPLES: list[str] — example input/output pairs")
    print("  • SYMPY_LOCALS: dict — symbols available in module")
    print("  • execute(task, expr, vars, eqs) → result | None")
    print("  • get_steps(task, expr, result) → str | None\n")


def print_environment_setup():
    """Print environment setup instructions."""
    print(f"\n{colorize('🔨 ENVIRONMENT SETUP', ANSI_BOLD_GREEN)}\n")
    
    print(f"{colorize('1. Install Python Dependencies:', ANSI_BOLD_YELLOW)}")
    print("   $ pip install sympy numpy\n")
    
    print(f"{colorize('2. Install & Run Ollama:', ANSI_BOLD_YELLOW)}")
    print("   $ ollama serve  (in one terminal)\n")
    
    print(f"{colorize('3. Pull Required Models:', ANSI_BOLD_YELLOW)}")
    print("   $ ollama pull qwen2-math:7b    (LLM for math)")
    print("   $ ollama pull nomic-embed-text (optional, for auto-detection)\n")
    
    print(f"{colorize('4. Clone & Test Deriva:', ANSI_BOLD_YELLOW)}")
    print("   $ git clone <repo> deriva")
    print("   $ cd deriva")
    print("   $ python main.py \"solve x + 5 = 10\"\n")


def print_full_help():
    """Print complete help documentation."""
    print_help_banner()
    print_quick_start()
    print_command_line_options()
    print_usage_examples()
    print_topic_routing()
    print_interactive_commands()
    print_features()
    print_requirements()
    print_environment_setup()
    print_configuration()
    print_advanced_usage()
    print_tips_and_tricks()
    print_api_reference()
    print_troubleshooting()
    
    # Footer
    print(f"\n{colorize('─' * 60, ANSI_DIM_WHITE)}")
    print(f"{colorize('For more help, visit: https://github.com/Mahmud-Mahi/Deriva', ANSI_DIM_WHITE)}")
    print(f"{colorize('Documentation: Read README.md, EMBEDDINGS_GUIDE.md', ANSI_DIM_WHITE)}")
    print(f"{colorize('Questions? Open an issue on GitHub', ANSI_DIM_WHITE)}\n")


def print_full_help_no_banner():
    """Print complete help documentation without banner (for interactive mode)."""
    print_quick_start()
    print_command_line_options()
    print_usage_examples()
    print_topic_routing()
    print_interactive_commands()
    print_features()
    print_requirements()
    print_environment_setup()
    print_configuration()
    print_advanced_usage()
    print_tips_and_tricks()
    print_api_reference()
    print_troubleshooting()
    
    # Footer
    print(f"\n{colorize('─' * 60, ANSI_DIM_WHITE)}")
    print(f"{colorize('For more help, visit: https://github.com/Mahmud-Mahi/Deriva', ANSI_DIM_WHITE)}")
    print(f"{colorize('Documentation: Read README.md, EMBEDDINGS_GUIDE.md', ANSI_DIM_WHITE)}")
    print(f"{colorize('Questions? Open an issue on GitHub', ANSI_DIM_WHITE)}\n")


def print_brief_help():
    """Print brief help (for --help flag)."""
    print_help_banner()
    print_quick_start()
    print_command_line_options()
    print("\nFor full documentation, run: python main.py --full-help\n")
