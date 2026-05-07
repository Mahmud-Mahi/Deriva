# Deriva User Manual

**Deriva — Precision in Every Step**

AI-Powered Symbolic Math Solver | Version 1.0 | Python 3.10+

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Topic Routing System](#topic-routing-system)
5. [Interactive Mode](#interactive-mode)
6. [Command-Line Options](#command-line-options)
7. [Examples](#examples)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Configuration](#configuration)
11. [API Reference](#api-reference)

---

## Quick Start

### 1. Install Requirements

```bash
# Python 3.10+
python --version

# Install dependencies
pip install sympy numpy

# Install and run Ollama
# Download from https://ollama.ai
ollama serve  # Keep running in background
```

### 2. Pull Models

```bash
# LLM for solving math problems (required)
ollama pull qwen2-math:7b

# Embedding model for auto-detection (optional but recommended)
ollama pull nomic-embed-text
```

### 3. Run Deriva

```bash
# Interactive mode
python main.py

# Solve single problem
python main.py "solve x^2 = 9"

# With topic specification
python main.py "/vector dot product of (1,2) and (3,4)"

# Show help
python main.py --help          # Brief help
python main.py --full-help     # Complete manual
```

---

## Installation

### Prerequisites

- **Python 3.10+** (check with `python --version`)
- **Ollama** (https://ollama.ai/) — runs LLM locally
- **SymPy** — symbolic math library
- **NumPy** — numerical computing (for embeddings)
- **2GB+ RAM** — for running LLM models
- **Internet** — optional, for downloading models

### Step-by-Step Setup

#### 1. Clone Repository

```bash
git clone <https://github.com/yourusername/deriva.git>
cd deriva
```

#### 2. Set Up Python Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# Or manually:
pip install sympy numpy
```

#### 3. Install Ollama

Download and install Ollama from https://ollama.ai

Start the Ollama server (keep it running):
```bash
ollama serve
```

#### 4. Pull Required Models

In a new terminal:
```bash
# Main math solver model
ollama pull qwen2-math:7b

# Optional: Semantic embeddings for auto-detection
ollama pull nomic-embed-text
```

#### 5. Test Installation

```bash
python main.py "2 + 2"
```

Expected output: Simple addition solved with step-by-step explanation.

---

## Basic Usage

### Interactive Mode

```bash
$ python main.py

∂>  solve x^2 - 9 = 0
[Solving equation...]

Final Answer:
-3, 3
```

Key features:
- Multi-line input (end with `\`)
- Command history (stored in `~/.cache/deriva_history`)
- Color-coded output
- Real-time "thinking..." indicator

### Single Query Mode

```bash
$ python main.py "simplify (x+1)^2 - (x-1)^2"

Final Answer:
4x
```

### With Topic Specification

```bash
$ python main.py "/algebra factor x^2 - 4"

Topic: /algebra

Final Answer:
(x - 2)(x + 2)
```

### Run with Options

```bash
# Use different model
$ python main.py -m neural-chat "solve 3x + 5 = 20"

# Custom Ollama URL
$ python main.py --ollama-url http://192.168.1.100:11434/api/generate "solve x = 5"

# Debug mode (show intermediate steps)
$ python main.py --debug "solve x^2 = 16"
```

---

## Topic Routing System

Deriva intelligently routes problems to specialized math modules for accuracy and performance.

### Three Routing Methods

#### 1. **Explicit Topic Prefix** (Guaranteed)

Fastest and most reliable. Syntax options:
- `/topic-name problem`
- `#topic-name problem`
- `topic-name: problem`

Examples:
```bash
$ python main.py "/vector dot product of (1,0,1) and (0,1,0)"
$ python main.py "#circle find center of x^2 + y^2 - 4x + 6y = 3"
$ python main.py "calculus: integrate x^3 dx"
```

#### 2. **Semantic Auto-Detection** (When nomic-embed-text available)

No prefix needed — Deriva understands the problem:

```bash
$ python main.py "find the tangent line to circle at (3,4)"
[auto-detected: /circle (78% confidence)]
```

Features:
- Shows confidence percentage
- Works for cross-domain problems
- Caches embeddings for speed

#### 3. **General Solver** (Fallback)

No topic specified, uses LLM to understand and route:

```bash
$ python main.py "solve x + 5 = 10"
```

### Available Topics

| Topic | Aliases | Description |
|-------|---------|-------------|
| `algebra` | — | Polynomial factoring, equation solving, expansion |
| `vector` | — | Dot product, cross product, vector operations |
| `circle` | — | Circle properties, tangent lines, intersections |
| `line`, `straight-line` | `straight_line` | Linear equations, slopes, intercepts |
| `conics` | — | Parabolas, ellipses, hyperbolas |
| `matrix` | — | Determinants, inverses, eigenvalues |
| `trigonometry`, `trig` | `inverse-trigonometry` | Trig functions, identities, inverse trig |
| `calculus` | — | Derivatives, integrals, limits, differential equations |
| `combination`, `permutation` | `permutation_combination` | Combinations, permutations, factorial |
| `geometry` | — | Areas, volumes, geometric calculations |

### Performance Tips

- **Explicit topic is fastest**: No embedding computation
- **Auto-detection slower on first query**: Computes embeddings (~2-3s)
- **Cached on repeated queries**: <100ms for same topics
- **Use `--debug` to see routing**: Shows which topic was selected

---

## Interactive Mode

### Commands

| Command | Description |
|---------|-------------|
| `exit` or `quit` | Close Deriva |
| `help` or `?` | Show available topics |
| `/topic problem` | Route to specific topic |
| `\\` at end of line | Continue to next line (multiline input) |
| `Ctrl+C` | Interrupt current operation |
| `Ctrl+D` | Exit (Unix/Mac) |

### Example Session

```bash
$ python main.py

Ollama Status: ONLINE
Model: qwen2-math:7b
Semantic Detection: enabled (nomic-embed-text)

--- Instructions ---
• Type 'exit' or 'quit' or press Ctrl+C to close.
• For MULTILINE input, end your line with a backslash (\) and press Enter.
• Use /topic prefix for explicit topic selection (e.g., '/vector solve |v|=5').

∂>  /algebra expand (x + 2)^3
Topic: /algebra

Solution steps:
(x + 2)³ = x³ + 3x²·2 + 3x·4 + 8

Final Answer:
x³ + 6x² + 12x + 8

∂>  /vector find magnitude of (3, 4)
Topic: /vector

Final Answer:
5

∂>  exit
Goodbye.
```

### Multiline Input

```bash
∂>  solve system:\
>  x + y = 5\
>  x - y = 1
[Solutions evaluated...]
```

---

## Command-Line Options

```bash
python main.py [OPTIONS] [PROMPT]
```

### Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `PROMPT` | Math problem to solve | `"solve x^2 = 4"` |
| `-m, --model` | LLM model to use | `-m neural-chat` |
| `--ollama-url` | Ollama API endpoint | `--ollama-url http://localhost:11434/api/generate` |
| `--debug` | Show debug information | `--debug` |
| `-h, --help` | Show brief help | — |
| `--full-help` | Show complete manual | — |

### Default Values

```bash
Model:       qwen2-math:7b
Ollama URL:  http://localhost:11434/api/generate
Debug:       OFF
```

---

## Examples

### Basic Algebra

```bash
$ python main.py "solve x^2 - 5x + 6 = 0"
Final Answer: 2, 3

$ python main.py "/algebra factor x^3 - 8"
Final Answer: (x - 2)(x² + 2x + 4)

$ python main.py "simplify sqrt(50)"
Final Answer: 5√2
```

### Vectors

```bash
$ python main.py "/vector dot product of (1,2,3) and (4,5,6)"
Final Answer: 32

$ python main.py "#vector magnitude of (3,4)"
Final Answer: 5

$ python main.py "/vector cross product (1,0,0) x (0,1,0)"
Final Answer: (0, 0, 1)
```

### Circle & Geometry

```bash
$ python main.py "find center of circle x^2 + y^2 - 4x + 6y = 3"
Final Answer: Center at (2, -3), Radius: 4

$ python main.py "#circle tangent line at (0,5) on x^2 + y^2 = 25"
Final Answer: y = 5
```

### Calculus

```bash
$ python main.py "derivative of x^3 + 2x^2 - 5x + 1"
Final Answer: 3x² + 4x - 5

$ python main.py "/calculus integrate x^2 dx"
Final Answer: x³/3

$ python main.py "solve differential equation dy/dx = 2x"
Final Answer: y = x² + C
```

### Trigonometry

```bash
$ python main.py "solve sin(x) = 0.5"
Final Answer: π/6 + 2πk, 5π/6 + 2πk

$ python main.py "/trig sin(π/4) + cos(π/4)"
Final Answer: √2
```

### Matrix Operations

```bash
$ python main.py "/matrix inverse of [[1,2],[3,4]]"
Final Answer: [[-2, 1], [1.5, -0.5]]

$ python main.py "#matrix determinant of [[a,b],[c,d]]"
Final Answer: ad - bc
```

### Combinations & Permutations

```bash
$ python main.py "/combination C(10,3)"
Final Answer: 120

$ python main.py "#permutation P(10,3)"
Final Answer: 720
```

---

## Advanced Features

### Semantic Embeddings

When `nomic-embed-text` is available, Deriva automatically understands problem intent:

```bash
$ python main.py "find where lines y=2x and y=5 intersect"
[auto-detected: /line (82% confidence)]

Solution routes to straight-line module with confidence shown.
```

Confidence levels:
- **75%+**: Highly confident, likely correct
- **60-74%**: Moderately confident
- **<60%**: Below threshold, uses general solver

### Custom Models

Switch between different Ollama models:

```bash
# Neural Chat (faster, good for algebra)
$ python main.py -m neural-chat "factor x^2 - 9"

# Mistral (powerful, good for calculus)
$ python main.py -m mistral "solve differential equation"

# Dolphin (specialized reasoning)
$ python main.py -m dolphin-mixtral "prove this identity"
```

Pull new models:
```bash
ollama pull neural-chat
ollama pull mistral
```

### Debug Mode

Shows intermediate steps and task structure:

```bash
$ python main.py --debug "solve x^2 = 16"

[DEBUG] Task: MathTask(
    operation='solve',
    equation='x^2 = 16',
    variables=['x'],
    ...
)

Solution steps:
[... detailed steps ...]

Final Answer:
-4, 4
```

### Batch Processing

Process multiple related problems:

```bash
$ python main.py "/algebra solve x^2 = 9 and x^3 = 27"

# Or pipe commands
$ echo "solve x + 5 = 10" | python main.py
```

### Environment Variables

```bash
# Set custom Ollama address
export OLLAMA_HOST=192.168.1.100:11434

# Timeout for requests (seconds)
export OLLAMA_TIMEOUT=300

# GPU acceleration
export OLLAMA_CUDA=1

# Then run Deriva
python main.py "solve x^2 = 4"
```

---

## Troubleshooting

### Problem: "Connection Lost: Unable to reach Ollama server"

**Causes:**
- Ollama not running
- Wrong URL specified
- Network issues

**Solutions:**
```bash
# 1. Start Ollama (if not running)
ollama serve

# 2. Verify connection
ollama list

# 3. Check custom URL
python main.py --ollama-url http://localhost:11434/api/generate "2 + 2"

# 4. Reset to default
python main.py --ollama-url http://localhost:11434/api/generate "test"
```

### Problem: "Model 'qwen2-math:7b' not found"

**Solution:**
```bash
# Pull the model
ollama pull qwen2-math:7b

# Verify
ollama list | grep qwen2-math
```

### Problem: "Semantic Detection: disabled"

**Causes:**
- `nomic-embed-text` not available

**Solutions:**
```bash
# Pull embedding model
ollama pull nomic-embed-text

# Restart Deriva
python main.py

# Or use explicit topics as fallback
python main.py "/vector solve problem"
```

### Problem: First query is very slow (3+ seconds)

**Diagnosis:**
- Normal for semantic embeddings (computing vectors)
- Subsequent queries use cache

**Solutions:**
- Expected on first run
- Use explicit `/topic` prefixes to skip embedding
- Embeddings cached in memory for 60+ seconds

### Problem: "Invalid math syntax" or parse errors

**Causes:**
- Using `**` instead of `^` for exponents
- Unescaped special characters
- Ambiguous notation

**Solutions:**
```bash
# Wrong
python main.py "x**2 + 3"

# Correct
python main.py "x^2 + 3"

# For equations, be explicit
python main.py "Eq(x^2, 9)"

# Use proper notation
python main.py "solve: x^2 - 9 = 0"  # Better
```

### Problem: Timeout errors or no response

**Causes:**
- Complex problem taking too long
- Model unresponsive
- Network latency

**Solutions:**
```bash
# Increase timeout
export OLLAMA_TIMEOUT=300
python main.py "complex problem"

# Try simpler problem first
python main.py "solve x = 5"

# Check Ollama logs
ollama logs

# Restart Ollama
# Kill current process and run: ollama serve
```

### Problem: Out of memory error

**Causes:**
- Running large LLM on low-end machine
- Multiple embeddings cached

**Solutions:**
```bash
# Use lighter model
python main.py -m neural-chat "solve x^2 = 4"

# Increase system swap (Linux)
sudo fallocate -l 4G /swapfile

# Reduce Ollama memory usage
export OLLAMA_MAX_LOADED_MODELS=1
```

### Problem: GUI/Display Issues

**Causes:**
- Terminal doesn't support ANSI colors
- Unicode character rendering issues

**Solutions:**
```bash
# Force color support
export TERM=xterm-256color
python main.py "solve x = 5"

# Or disable colors (create wrapper script)
python main.py --no-color "solve x = 5"
```

---

## Configuration

### Environment Variables

```bash
# Ollama Configuration
OLLAMA_HOST           # Custom Ollama address (default: localhost:11434)
OLLAMA_TIMEOUT        # Request timeout in seconds (default: 120)
OLLAMA_CUDA           # Enable CUDA acceleration (default: auto-detect)
OLLAMA_CPU_NUM_THREAD # CPU threads (default: all available)
```

### History and Cache

```bash
# Command history stored in:
~/.cache/deriva_history

# Embeddings cached in memory
# Persists only during session

# Clear history
rm ~/.cache/deriva_history
```

### Customization

Edit `embeddings.py` to customize:
- Topic descriptions (for better auto-detection)
- Similarity threshold (default: 0.55)
- Embedding cache behavior

Edit `modules/*` to:
- Add new math rules
- Provide examples for LLM
- Define execution logic

---

## API Reference

### Classes

#### `MathTask`

Represents a structured math problem:

```python
@dataclass
class MathTask:
    operation: str              # 'solve', 'simplify', 'integrate', etc.
    expression: str             # Main expression: "x^2 + 3x + 2"
    equation: str               # Single equation: "x^2 = 9"
    equations: list[str]        # Multiple equations
    variable: str               # Primary variable: 'x'
    variables: list[str]        # Multiple variables: ['x', 'y']
    lower_bound: str            # For integrals: '0'
    upper_bound: str            # For integrals: '10'
    point: str                  # For derivatives: '(3, 4)'
    direction: str              # For limits: '+-'
```

#### `EmbeddingEngine`

Handles semantic embeddings:

```python
from embeddings import EmbeddingEngine

engine = EmbeddingEngine(base_url="http://localhost:11434")

# Check availability
if engine.check_model_available():
    print("Ready!")

# Get embedding
vec = engine.embed("solve x^2 = 4")

# Find topic
topic, score = engine.find_best_topic(
    "find tangent line",
    TOPIC_DESCRIPTIONS,
    threshold=0.55
)
```

### Functions

#### `make_task(problem, model, url) → MathTask`

Converts natural language to structured task.

#### `solve_with_sympy(task) → Any`

Solves using SymPy and falls back to module logic.

#### `execute_topic_task(topic, problem, model, url) → tuple`

Routes through specific topic module.

#### `detect_topic_by_embedding(problem, engine) → tuple | None`

Returns `(topic, confidence_score)` or None.

### Module Interface

Create custom math modules with:

```python
# In modules/your_module.py

RULES = [
    "Rule 1 for LLM guidance",
    "Rule 2: specific constraint",
]

EXAMPLES = [
    "Example input and output pairs",
    "for LLM to learn from",
]

SYMPY_LOCALS = {
    "custom_func": custom_function,
}

def execute(task, expr, variables, equations):
    """Custom execution logic. Return None to skip."""
    if task.operation == "special_op":
        return solve_specially(expr)
    return None

def get_steps(task, expr_str, result):
    """Return human-readable solution steps."""
    return f"Step 1: ...\nStep 2: {result}"
```

Then register in `modules/__init__.py`:

```python
TOPIC_TO_MODULE["new_topic"] = your_module
MODULES.append(your_module)
```

---

## Tips & Tricks

1. **Use `/` prefix for speed** — Skips embedding computation
2. **Check confidence %** — Understand auto-detection reliability
3. **Enable `--debug`** — See intermediate computations
4. **Batch by topic** — Embeddings cached for reuse
5. **Use `\` for multiline** — Complex equation input
6. **Save commands** — History auto-stored in `~/.cache/deriva_history`
7. **Stack operations** — Chain: solve, then integrate result
8. **Predefine variables** — Let x, y, z be symbols upfront
9. **Use SymPy notation** — Familiar syntax: `sqrt()`, `sin()`, `Matrix()`
10. **Check `ollama list`** — Verify available models

---

## Getting Help

- **Brief help**: `python main.py --help`
- **Full manual**: `python main.py --full-help`
- **Interactive help**: Type `?` or `help` in interactive mode
- **Documentation**: Read `README.md` and `EMBEDDINGS_GUIDE.md`
- **Issues**: GitHub repository issue tracker
- **Questions**: Community forums or discussions

---

**Version 1.0 | Built with SymPy | Powered by Ollama**

For the latest updates, visit: https://github.com/yourusername/deriva
