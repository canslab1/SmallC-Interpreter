# Contributing to SmallC-Interpreter

Thank you for your interest in contributing to SmallC-Interpreter! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Issues

If you find a bug or have a feature suggestion:

1. Check the [existing issues](https://github.com/canslab1/SmallC-Interpreter/issues) to avoid duplicates.
2. Open a new issue with a clear title and detailed description.
3. For bugs, include: steps to reproduce, expected behavior, actual behavior, and your Python version.
4. For language features, provide example Small-C code demonstrating the desired behavior.

### Code Contributions

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Make your changes and test thoroughly.
4. Commit with clear, descriptive messages.
5. Push to your fork and open a Pull Request.

### Development Setup

```bash
git clone https://github.com/canslab1/SmallC-Interpreter.git
cd SmallC-Interpreter
python3 main.py
```

No virtual environment or third-party packages are needed — the project runs entirely on the Python 3.10+ standard library.

### Testing

Before submitting changes, verify your modifications against the test programs in `examples/` and ensure all REPL commands function correctly:

```bash
python3 main.py
sc> LOAD examples/factorial.c
sc> RUN
sc> LOAD examples/fibonacci.c
sc> RUN
```

### Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines.
- Use type hints for function signatures.
- Add docstrings to all public classes and methods.
- Keep modules focused: each file should have a single, clear responsibility.

## Questions

If you have questions about the project, feel free to [open an issue](https://github.com/canslab1/SmallC-Interpreter/issues) with the "question" label.
