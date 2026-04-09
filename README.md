# SmallC-Interpreter

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/License-MIT-green)
[![CANS Lab](https://img.shields.io/badge/CANS_Lab-Homepage-orange)](https://canslab1.github.io/)

## Overview

**SmallC-Interpreter** is a fully-featured interactive interpreter for the **Small-C** programming language, a strict subset of ISO C originally defined by Ron Cain (1980) and James Hendrix (1984). The interpreter provides a REPL (Read-Eval-Print Loop) environment similar to classic BASIC interpreters, where users can enter Small-C code line by line for immediate execution, or load complete source files for batch execution.

This project is developed as the final project for the **System Software** course (Spring 2026) at Chang Gung University. It integrates and extends core system software techniques — including symbol table management, lexical analysis, syntax-directed processing, and runtime environment simulation — bridging the gap from assembly language processors to high-level language interpreters.

The interpreter is implemented entirely in **Python 3** with no third-party dependencies, allowing students to focus on the core logic of language processing rather than low-level memory management details.

## Features

- **Interactive REPL** — Enter Small-C code at the `sc>` prompt with automatic multi-line continuation for blocks, loops, and functions
- **Program Buffer Management** — Full set of editing commands (`LOAD`, `SAVE`, `LIST`, `EDIT`, `DELETE`, `INSERT`, `APPEND`, `NEW`) for in-environment source code development
- **Recursive-Descent Parser** — Complete operator precedence handling across 13 levels with proper associativity
- **Tree-Walking Interpreter** — Direct AST execution with support for nested scopes and recursive function calls
- **Simulated Memory Model** — Byte-addressable memory supporting arrays, pointers, pointer arithmetic, and address-of operations
- **23 Built-in Functions** — I/O (`printf`, `scanf`, `putchar`, `getchar`, `puts`), string (`strlen`, `strcpy`, `strcmp`, `strcat`), math (`abs`, `max`, `min`, `pow`, `sqrt`, `mod`, `rand`, `srand`), and utility (`memset`, `atoi`, `itoa`, `sizeof_int`, `sizeof_char`, `exit`)
- **Execution Tracing** — `TRACE ON/OFF` mode displays each statement with line numbers during execution for debugging
- **State Inspection** — `VARS` command shows all global variables with types and values; `FUNCS` lists user-defined and built-in functions
- **Syntax Checking** — `CHECK` command validates source code without executing
- **Comprehensive Error Handling** — Clear syntax error and runtime error messages with line numbers (division by zero, array bounds checking, type errors)
- **Preprocessor** — `#define` constant macro expansion
- **Comments** — Both C-style block comments (`/* */`) and C++ single-line comments (`//`)

## Supported Language Features

| Category | Features |
|----------|----------|
| **Data Types** | `int` (32-bit signed), `char` (8-bit signed), `int*`, `char*` |
| **Constants** | Decimal integers, hexadecimal (`0xFF`), character literals (`'A'`), string literals (`"hello"`) with escape sequences (`\n`, `\t`, `\0`, `\\`, `\'`, `\"`) |
| **Operators** | Arithmetic (`+`, `-`, `*`, `/`, `%`), relational (`<`, `<=`, `>`, `>=`, `==`, `!=`), logical (`&&`, `\|\|`, `!`), bitwise (`&`, `\|`, `^`, `~`, `<<`, `>>`), assignment (`=`, `+=`, `-=`, `*=`, `/=`, `%=`), prefix increment/decrement (`++`, `--`) |
| **Control Flow** | `if`/`else` (with chaining), `while`, `for`, `do`/`while`, `break`, `continue`, `return`, `switch`/`case` (bonus) |
| **Functions** | User-defined with `int`/`char`/`void` return types, call-by-value, pointer parameters, recursion |
| **Arrays** | One-dimensional with compile-time size, zero-indexed, bounds checking |
| **Pointers** | Address-of (`&`), dereference (`*`), pointer arithmetic |

## Installation

### Prerequisites

- Python 3.10 or higher

### Setup

```bash
git clone https://github.com/canslab1/SmallC-Interpreter.git
cd SmallC-Interpreter
```

No additional dependencies are required — the interpreter runs entirely on the Python standard library.

## Usage

### Starting the Interpreter

```bash
python3 main.py
```

The interpreter displays a welcome banner and enters interactive mode:

```
==============================================
  Small-C Interactive Interpreter v1.0
  System Software Final Project, Spring 2026
==============================================
Type 'HELP' for a list of commands.

sc>
```

### Interactive Mode

Enter Small-C statements directly at the prompt for immediate execution:

```
sc> printf("%d\n", 2 + 3 * 4);
14
sc> int x = 42;
sc> printf("x = %d\n", x);
x = 42
```

Multi-line constructs (functions, loops, conditionals) are automatically detected — the prompt changes to `  >` until all braces are balanced:

```
sc> int factorial(int n) {
  >     if (n <= 1) return 1;
  >     return n * factorial(n - 1);
  > }
sc> printf("5! = %d\n", factorial(5));
5! = 120
```

### Program Buffer Mode

Use `APPEND` to enter a complete program, then `RUN` to execute:

```
sc> APPEND
   1> int main() {
   2>     int i;
   3>     for (i = 1; i <= 5; i = i + 1) {
   4>         printf("%d ", i * i);
   5>     }
   6>     printf("\n");
   7>     return 0;
   8> }
   9> .
sc> RUN
1 4 9 16 25
Program exited with return value 0.
```

### Environment Commands

| Command | Description |
|---------|-------------|
| `LOAD <file>` | Load source file into program buffer |
| `SAVE <file>` | Save buffer contents to file |
| `LIST [n\|n1-n2]` | Display buffer contents (all, single line, or range) |
| `EDIT <n>` | Edit a specific line |
| `DELETE <n\|n1-n2>` | Delete line(s) from buffer |
| `INSERT <n>` | Insert lines before line n |
| `APPEND` | Append lines to end of buffer |
| `NEW` | Clear buffer and reset all state |
| `RUN` | Execute the program from `main()` |
| `CHECK` | Syntax check without executing |
| `TRACE ON\|OFF` | Toggle execution tracing |
| `VARS` | Display all global variables |
| `FUNCS` | List all defined functions |
| `HELP [cmd]` | Show help information |
| `ABOUT` | Show version and author info |
| `CLEAR` | Clear terminal screen |
| `QUIT` / `EXIT` | Exit the interpreter |

## Project Structure

```
SmallC-Interpreter/
├── main.py                 # Entry point
├── pyproject.toml          # Project metadata
├── requirements.txt        # Dependencies (none required)
├── LICENSE                 # MIT License
├── CHANGELOG.md            # Version history
├── CONTRIBUTING.md         # Contribution guidelines
├── CITATION.cff            # Citation metadata
├── smallc/                 # Main package
│   ├── __init__.py         # Version and metadata
│   ├── tokens.py           # Token types and keyword definitions
│   ├── lexer.py            # Lexical analyzer (tokenizer)
│   ├── preprocessor.py     # #define macro expansion
│   ├── ast_nodes.py        # Abstract Syntax Tree node definitions
│   ├── parser.py           # Recursive-descent parser
│   ├── memory.py           # Simulated byte-addressable memory
│   ├── symtable.py         # Symbol table with scope chain
│   ├── builtins.py         # 23 built-in library functions
│   ├── interpreter.py      # Tree-walking interpreter with TRACE
│   └── repl.py             # Interactive REPL environment
└── examples/               # Sample Small-C programs
    ├── hello.c             # Hello World
    ├── factorial.c         # Recursive factorial
    ├── fibonacci.c         # Fibonacci with arrays and #define
    └── pointers.c          # Pointer operations and dynamic memory
```

## Architecture

The interpreter follows a classic pipeline architecture:

```
Source Code → Preprocessor → Lexer → Parser → AST → Interpreter → Output
                                                        ↕
                                                  Memory Model
                                                  Symbol Table
                                                  Built-in Functions
```

| Module | Responsibility |
|--------|---------------|
| `preprocessor.py` | Expands `#define` constant macros |
| `lexer.py` | Tokenizes source code into a stream of typed tokens |
| `parser.py` | Builds an AST using recursive descent with 13-level operator precedence |
| `memory.py` | Simulates flat byte-addressable memory (64 KB) with variable and heap regions |
| `symtable.py` | Manages variable symbols with lexical scope chains |
| `interpreter.py` | Walks the AST to execute statements, with TRACE and debug support |
| `builtins.py` | Implements all 23 standard library functions |
| `repl.py` | Provides the interactive shell with program buffer management |

## Authors

- **黃崇源 (Chung-Yuan Huang)** — Associate Professor, Department of Computer Science and Information Engineering, Chang Gung University, Taiwan (gscott@mail.cgu.edu.tw)

## Citation

If you use this software in your work, please cite it as follows:

> Huang, C.-Y. (2026). SmallC-Interpreter: A Small-C Interactive Interpreter for System Software Education. Chang Gung University. https://github.com/canslab1/SmallC-Interpreter

See [`CITATION.cff`](CITATION.cff) for machine-readable citation metadata.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
