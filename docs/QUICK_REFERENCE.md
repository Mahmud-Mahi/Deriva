#!/usr/bin/env markdown
# Deriva Quick Reference Card

**Print this page or save as PDF for quick access!**

---

## Installation (5 minutes)

```bash
pip install sympy numpy
ollama pull qwen2-math:7b
ollama pull nomic-embed-text    # Optional, for auto-detection
ollama serve                    # Keep running

# In another terminal:
python main.py --help
```

---

## Running Deriva

### Quick Start
```bash
python main.py "solve x^2 = 9"          # Single query
python main.py                          # Interactive mode
python main.py --help                   # Show help
python main.py --full-help              # Show complete manual
```

### With Options
```bash
python main.py -m neural-chat "problem" # Use different model
python main.py --debug "problem"        # Show debug info
```

---

## Math Topics (11 Available)

| Syntax | Topic | Example |
|--------|-------|---------|
| `/algebra` | Polynomials, equations | `factor x^2 - 4` |
| `/vector` | Vector operations | `dot product of (1,2) and (3,4)` |
| `/circle` | Circle geometry | `center of x^2 + y^2 - 4x = 0` |
| `/line` | Linear equations | `slope of 2x + 3y = 6` |
| `/conics` | Conic sections | `focus of y^2 = 4x` |
| `/matrix` | Matrix operations | `inverse of [[1,2],[3,4]]` |
| `/trig` | Trigonometry | `solve sin(x) = 0.5` |
| `/calculus` | Derivatives, etc. | `integrate x^2 dx` |
| `/combination` | Permutations | `C(10,3)` or `P(10,3)` |
| `/geometry` | Area, volume | `area of circle radius 5` |

---

## Interactive Commands

| Command | Description |
|---------|-------------|
| `exit`, `quit` | Close Deriva |
| `help`, `?` | Show available topics |
| `/TOPIC problem` | Route to specific topic |
| `\` at line end | Continue multiline input |
| `Ctrl+C` | Interrupt |

---

## Example Usage

### Algebra
```bash
python main.py "solve 3x + 5 = 20"
python main.py "/algebra factor x^3 - 8"
```

### Vectors
```bash
python main.py "/vector dot product of (1,2,3) and (4,5,6)"
python main.py "#vector magnitude of (3,4,5)"
```

### Calculus
```bash
python main.py "derivative of x^3 + 2x"
python main.py "/calculus integrate x^2 from 0 to 2"
```

### Systems
```bash
python main.py "solve x+y=5 and x-y=1"
```

---

## Semantic Auto-Detection

```bash
# No prefix needed! Deriva understands intent
python main.py "find the tangent line to circle x^2 + y^2 = 25 at (3,4)"
# Output: [auto-detected: /circle (82% confidence)]
```

- 75%+ confidence → Use it
- 60-74% confidence → Maybe override
- <60% confidence → Not detected

---

## Syntax Tips

| Problem | Solving |
|---------|---------|
| Exponents | Use `^` not `**`: `x^2`, not `x**2` |
| Multiplication | Use `*`: `2*x`, `sin(x)*cos(x)` |
| Division | Use `/`: `x/2` |
| Functions | `sin()`, `cos()`, `tan()`, `log()`, `sqrt()` |
| Equations | `Eq(x^2, 9)` or use `=` in quotes |
| Variables | `x`, `y`, `z`, `t`, etc. |
| Constants | `pi`, `E`, `I` (for imaginary) |
| Special | `oo` (infinity), `sqrt()`, `factorial()` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "Connection Lost" | `ollama serve` (need Ollama running) |
| "Model not found" | `ollama pull qwen2-math:7b` |
| "Semantic Detection: disabled" | `ollama pull nomic-embed-text` |
| Slow first query | Normal (computing embeddings), use `/topic` |
| Parse error | Check syntax, use `^` for powers |
| Timeout | Complex problem, try simpler one first |

---

## Environment Variables

```bash
export OLLAMA_HOST=localhost:11434      # Custom Ollama address
export OLLAMA_TIMEOUT=300               # Request timeout (seconds)
export OLLAMA_CUDA=1                    # Enable GPU acceleration
```

---

## Advanced Usage

### Custom Model
```bash
python main.py -m mistral "solve x^3 = 8"
python main.py -m neural-chat "integrate"
# Pull models: ollama pull <model-name>
```

### Debug Mode
```bash
python main.py --debug "solve x^2 = 16"
# Shows: MathTask structure, computation steps, timing
```

### Custom Ollama URL
```bash
python main.py --ollama-url http://192.168.1.100:11434/api/generate "2+2"
```

---

## Help System

```bash
python main.py --help          # Brief help (50 lines)
python main.py --full-help     # Complete manual (200+ lines)
cat USER_MANUAL.md             # Read offline manual
grep "vector" USER_MANUAL.md   # Search by keyword
```

---

## Performance Tips

| Tip | Benefit |
|-----|---------|
| Use `/topic` prefix | Skip embedding computation (fast) |
| Batch similar problems | Embeddings cached (~100ms each) |
| Use `--debug` | See what's happening |
| Enable GPU | `export OLLAMA_CUDA=1` |
| Use lighter model | `neural-chat` faster than `qwen2-math` |

---

## Keyboard Shortcuts (Interactive Mode)

| Key | Action |
|-----|--------|
| `↑` | Previous command |
| `↓` | Next command |
| `Ctrl+A` | Start of line |
| `Ctrl+E` | End of line |
| `Ctrl+K` | Clear line |
| `Ctrl+C` | Interrupt |
| `Ctrl+D` | Exit (Unix/Mac) |

---

## File Locations

```bash
~/.cache/deriva_history         # Command history (auto-saved)
./USER_MANUAL.md               # Complete offline manual
./help_system.py               # Help implementation
./embeddings.py                # Semantic embeddings
./modules/                     # Math domain implementations
```

---

## Common Problems & Fixes

### Slow Performance
```bash
# Use topic prefix (avoids embedding):
python main.py "/algebra factor x^2 - 4"

# Or use lighter model:
python main.py -m neural-chat "problem"
```

### Wrong Topic Detected
```bash
# Override with explicit prefix:
python main.py "/vector dot product..."
```

### Memory Issues
```bash
# Reduce loaded models in Ollama:
export OLLAMA_MAX_LOADED_MODELS=1

# Use CPU-only:
export OLLAMA_CUDA=0
```

---

## One-Liner Examples

```bash
# Algebra
python main.py "solve (x-3)(x+2) = 0"

# Vectors  
python main.py "/vector magnitude of (6,8)"

# Calculus
python main.py "#calculus derivative of sin(x) + cos(x)"

# Matrix
python main.py "matrix: trace of [[1,2],[3,4]]"

# Combinations
python main.py "combination: C(52,5) for poker hands"

# Geometry
python main.py "geometry: area of parallelogram base 5 height 3"
```

---

## Getting Help

| Need | Command |
|------|---------|
| Quick help | `python main.py --help` |
| Full manual | `python main.py --full-help` |
| Search docs | `grep "search term" USER_MANUAL.md` |
| Interactive | `∂> help` or `∂> ?` |
| View manual | `less USER_MANUAL.md` |

---

## Quick Topic Lookup

**Algebra**: factor, expand, solve, simplify
**Vector**: magnitude, dot product, cross product
**Circle**: center, radius, tangent line, chord
**Line**: find slope, equation, intercept
**Conics**: parabola, ellipse, hyperbola, focus
**Matrix**: inverse, determinant, eigenvalues
**Trig**: sin, cos, tan, identities, solve
**Calculus**: derivative, integral, limit, differential equation
**Combo**: permutation, combination, factorial
**Geometry**: area, perimeter, volume

---

## Pro Tips

1. **Prefix is fastest** → `/topic` skips AI inference
2. **Show confidence** → Auto-detected topics show % confidence
3. **Stack problems** → Solve result, then integrate/differentiate
4. **Use history** → Up arrow recalls previous queries
5. **Save session** → History stored in `~/.cache/deriva_history`
6. **Try examples** → Run each to see formats
7. **Check debug** → `--debug` shows computation process
8. **Explore topics** → Each has specialized rules
9. **Read manual** → `USER_MANUAL.md` has 100+ examples
10. **Have fun!** → Math solving with AI is powerful

---

**Print this card • Bookmark this page • Share with friends**

For complete documentation: `python main.py --full-help`
