# Deriva — Precision in Every Step

**Deriva** is a powerful CLI-based math engine that combines symbolic computation with AI-assisted problem understanding.
It converts natural math problems into structured expressions, solves them using SymPy, and presents results in beautifully formatted output.

---

## ✨ Features

* 🔍 **Natural Language → Math**

  * Uses LLM (via Ollama) to convert problems into structured SymPy tasks

* 🧮 **Symbolic Computation**

  * Solve equations, simplify expressions, and handle multi-variable systems

* 📜 **Step-by-Step Solutions**

  * Generates human-readable solution steps for better understanding

* 🎨 **Beautiful Math Formatting**

  * Custom formatter for:

    * Fractions (vertical layout)
    * Powers (superscripts)
    * Roots, matrices, and more

* ⚡ **Interactive CLI**

  * Multi-line input support
  * Command history
  * Real-time "thinking..." indicator

---

## ⚙️ Requirements

* Python 3.10+
* Ollama installed and running
* A math-capable model (default: `qwen2-math:7b`)

---

## 🚀 Installation

```bash
git clone https://github.com/your-username/deriva.git
cd deriva
pip install sympy
python3 main.py
```

---

## 🧠 Run Ollama

Make sure Ollama is running:

```bash
ollama serve
ollama run qwen2-math:7b
```

---

## ▶️ Usage

### Run interactively:

```bash
python main.py
```

### Run a single query:

```bash
python main.py "solve x^2 - 4 = 0"
```

### Options:

```bash
-m, --model        Choose model (default: qwen2-math:7b)
--ollama-url       Ollama API URL
--debug            Show debug information
```

---

## 🧩 Project Structure

```
deriva/
│── main.py        # CLI + pipeline orchestration
│── models.py      # Task schema (MathTask)
│── formatter.py   # Custom math formatting engine
│── modules/       # Rules, execution logic, examples
```

---

## 🛠️ How It Works

1. User inputs a math problem
2. LLM converts it → structured JSON (`MathTask`)
3. SymPy parses and solves it
4. Formatter renders clean mathematical output
5. Steps + final answer are displayed

---

## 🎯 Example Capabilities

* Solve equations:

  ```
  solve 2x + 3 = 7
  ```

* Simplify expressions:

  ```
  simplify (x^2 - 1)/(x - 1)
  ```

* Systems of equations:

  ```
  solve:
  x + y = 5
  x - y = 1
  ```

---

## ⚠️ Limitations

* Depends on LLM accuracy for parsing
* Requires Ollama to be running locally
* Not all math domains are fully supported (yet 😉)

---

## 🔮 Future Plans

* Graph plotting
* More advanced calculus support
* Better natural language understanding
* Plugin system for custom math modules
* Physics math support

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork, improve, and submit a pull request.

---

## 📜 License

MIT License

---

## 👤 Auther

[Mahmud Mahi](mailto:mahmudurahmanmahi26@gmail.com)

---

## 💡 Philosophy

> Math isn’t just about answers — it’s about understanding the journey.
> **Deriva focuses on both.**
