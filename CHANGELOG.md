# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## v1.0.0 (2026-04-09)

### Added

- **Lexer** — Tokenizer supporting all Small-C tokens: keywords, identifiers, integer/hex literals, char/string literals with escape sequences, operators (13 precedence levels), and delimiters
- **Preprocessor** — `#define` constant macro expansion with word-boundary-aware substitution
- **Parser** — Recursive-descent parser producing a complete AST, supporting all Small-C control structures (`if`/`else`, `while`, `for`, `do`/`while`, `switch`/`case`, `break`, `continue`, `return`), variable declarations, function definitions, and the full C operator precedence hierarchy
- **Memory model** — Simulated 64 KB byte-addressable memory with separate variable storage (starting at address 1024) and heap region (starting at address 32768), supporting `int` (4-byte) and `char` (1-byte) read/write operations
- **Symbol table** — Scope-chained environment with lexical scoping for variable lookup, declaration, and assignment
- **Interpreter** — Tree-walking evaluator with visitor pattern, supporting all AST node types, array bounds checking, pointer dereference/address-of operations, and C-style integer division (truncation toward zero)
- **23 built-in functions** — I/O (`printf`, `scanf`, `putchar`, `getchar`, `puts`), string (`strlen`, `strcpy`, `strcmp`, `strcat`), math (`abs`, `max`, `min`, `pow`, `sqrt`, `mod`, `rand`, `srand`), and utility (`memset`, `atoi`, `itoa`, `sizeof_int`, `sizeof_char`, `exit`)
- **Interactive REPL** — `sc>` prompt with automatic multi-line continuation detection (brace/parenthesis/bracket balancing, block comment tracking), supporting direct statement execution in global scope
- **Program buffer management** — `LOAD`, `SAVE`, `LIST` (all/single/range), `EDIT`, `DELETE` (single/range), `INSERT`, `APPEND`, `NEW` commands with unsaved-changes confirmation prompts
- **Execution commands** — `RUN` (execute from `main()`), `CHECK` (syntax validation), `TRACE ON`/`OFF` (line-by-line execution tracing with call-depth indentation)
- **State inspection** — `VARS` (display global variables with types, values, array contents, pointer addresses) and `FUNCS` (list user-defined functions with signatures and line numbers, plus all built-in functions)
- **System commands** — `HELP` (summary and per-command detail), `ABOUT`, `CLEAR`, `QUIT`/`EXIT`
- **Error handling** — Distinct `Syntax error:` and `Runtime error:` message formats with contextual details (array index and size for bounds violations, function name for argument errors)
- **Example programs** — `hello.c`, `factorial.c`, `fibonacci.c`, `pointers.c`
