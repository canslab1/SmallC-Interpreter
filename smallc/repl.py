"""Interactive REPL (Read-Eval-Print Loop) for the Small-C interpreter."""

import os
import sys

from . import __version__, __author__, __semester__
from .errors import SmallCError, StopExecution
from .interpreter import Interpreter
from .lexer import Lexer
from .parser import Parser
from .preprocessor import Preprocessor


PROMPT = "sc> "
CONTINUE_PROMPT = "  > "


class REPL:
    """Small-C interactive interpreter environment."""

    def __init__(self):
        self.interpreter = Interpreter()
        self.buffer: list[str] = []       # program buffer (1-indexed conceptually)
        self.modified: bool = False       # unsaved changes flag
        self._output_parts: list[str] = []

        # Wire interpreter I/O
        self.interpreter._output = self._write_output
        self.interpreter._input = self._read_input
        self.interpreter.builtins._out = self._write_output
        self.interpreter.builtins._in = self._read_input

    def _write_output(self, text: str):
        """Collect output, print immediately without extra newline."""
        sys.stdout.write(text)
        sys.stdout.flush()

    def _read_input(self) -> str:
        """Read input from user."""
        try:
            return input()
        except EOFError:
            return ""

    # ── main loop ──

    def run(self):
        self._print_banner()
        while True:
            try:
                line = self._read_multiline()
                if line is None:
                    continue
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                # Check if it's a command
                if self._try_command(line_stripped):
                    continue
                # Treat as Small-C code: execute interactively
                self._execute_interactive(line_stripped)
            except KeyboardInterrupt:
                print()
            except EOFError:
                print("\nGoodbye.")
                break

    # ── multi-line input ──

    def _read_multiline(self) -> str | None:
        """Read input, continuing with '  > ' prompt if braces/parens are unbalanced."""
        try:
            first = input(PROMPT)
        except EOFError:
            raise
        except KeyboardInterrupt:
            print()
            return None

        lines = [first]
        # Check if we need continuation
        while self._needs_continuation('\n'.join(lines)):
            try:
                cont = input(CONTINUE_PROMPT)
            except EOFError:
                break
            except KeyboardInterrupt:
                print()
                return None
            lines.append(cont)

        return '\n'.join(lines)

    def _needs_continuation(self, text: str) -> bool:
        """Check if the input is incomplete (unbalanced braces, etc.)."""
        # Count braces/parens/brackets
        brace = 0
        paren = 0
        bracket = 0
        in_string = False
        in_char = False
        in_line_comment = False
        in_block_comment = False
        i = 0
        while i < len(text):
            ch = text[i]
            if in_line_comment:
                if ch == '\n':
                    in_line_comment = False
            elif in_block_comment:
                if ch == '*' and i + 1 < len(text) and text[i+1] == '/':
                    in_block_comment = False
                    i += 1
            elif in_string:
                if ch == '\\':
                    i += 1  # skip escaped char
                elif ch == '"':
                    in_string = False
            elif in_char:
                if ch == '\\':
                    i += 1
                elif ch == "'":
                    in_char = False
            else:
                if ch == '/' and i + 1 < len(text) and text[i+1] == '/':
                    in_line_comment = True
                    i += 1
                elif ch == '/' and i + 1 < len(text) and text[i+1] == '*':
                    in_block_comment = True
                    i += 1
                elif ch == '"':
                    in_string = True
                elif ch == "'":
                    in_char = True
                elif ch == '{':
                    brace += 1
                elif ch == '}':
                    brace -= 1
                elif ch == '(':
                    paren += 1
                elif ch == ')':
                    paren -= 1
                elif ch == '[':
                    bracket += 1
                elif ch == ']':
                    bracket -= 1
            i += 1

        if in_block_comment:
            return True
        if brace > 0 or paren > 0 or bracket > 0:
            return True
        return False

    # ── command dispatch ──

    def _try_command(self, line: str) -> bool:
        """Try to parse and execute a REPL command. Returns True if it was a command."""
        upper = line.upper()
        word = upper.split()[0] if upper.split() else ""
        rest = line[len(word):].strip()

        cmd_map = {
            'LOAD': self._cmd_load,
            'SAVE': self._cmd_save,
            'LIST': self._cmd_list,
            'EDIT': self._cmd_edit,
            'DELETE': self._cmd_delete,
            'INSERT': self._cmd_insert,
            'APPEND': self._cmd_append,
            'NEW': self._cmd_new,
            'RUN': self._cmd_run,
            'CHECK': self._cmd_check,
            'VARS': self._cmd_vars,
            'FUNCS': self._cmd_funcs,
            'HELP': self._cmd_help,
            'ABOUT': self._cmd_about,
            'CLEAR': self._cmd_clear,
            'QUIT': self._cmd_quit,
            'EXIT': self._cmd_quit,
        }

        if word == 'TRACE':
            self._cmd_trace(rest)
            return True

        if word in cmd_map:
            cmd_map[word](rest)
            return True

        return False

    # ── program management commands ──

    def _cmd_load(self, arg: str):
        filename = arg.strip()
        if not filename:
            print("Usage: LOAD <filename>")
            return
        if self.modified:
            if not self._confirm("Buffer has unsaved changes. Discard? (y/n) "):
                return
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.buffer = f.read().splitlines()
            self.modified = False
            print(f"Loaded {len(self.buffer)} lines from '{filename}'.")
        except FileNotFoundError:
            print(f"Error: file '{filename}' not found.")
        except IOError as e:
            print(f"Error: cannot open '{filename}': {e}")

    def _cmd_save(self, arg: str):
        filename = arg.strip()
        if not filename:
            print("Usage: SAVE <filename>")
            return
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.buffer))
                if self.buffer:
                    f.write('\n')
            self.modified = False
            print(f"Saved {len(self.buffer)} lines to '{filename}'.")
        except IOError as e:
            print(f"Error: cannot write '{filename}': {e}")

    def _cmd_list(self, arg: str):
        if not self.buffer:
            print("Buffer is empty.")
            return
        arg = arg.strip()
        if not arg:
            for i, line in enumerate(self.buffer, 1):
                print(f"{i:4d}: {line}")
        elif '-' in arg:
            parts = arg.split('-', 1)
            try:
                n1, n2 = int(parts[0].strip()), int(parts[1].strip())
                for i in range(n1, min(n2 + 1, len(self.buffer) + 1)):
                    print(f"{i:4d}: {self.buffer[i-1]}")
            except (ValueError, IndexError):
                print("Usage: LIST <n1>-<n2>")
        else:
            try:
                n = int(arg)
                if 1 <= n <= len(self.buffer):
                    print(f"{n:4d}: {self.buffer[n-1]}")
                else:
                    print(f"Line {n} is out of range (1-{len(self.buffer)}).")
            except ValueError:
                print("Usage: LIST [n] or LIST [n1]-[n2]")

    def _cmd_edit(self, arg: str):
        try:
            n = int(arg.strip())
        except ValueError:
            print("Usage: EDIT <n>")
            return
        if n < 1 or n > len(self.buffer):
            print(f"Line {n} is out of range (1-{len(self.buffer)}).")
            return
        print(f"{n:4d}: {self.buffer[n-1]}")
        try:
            new_line = input(f"{n:4d}: ")
            if new_line:  # only replace if user typed something
                self.buffer[n-1] = new_line
                self.modified = True
        except (EOFError, KeyboardInterrupt):
            print()

    def _cmd_delete(self, arg: str):
        arg = arg.strip()
        if '-' in arg:
            parts = arg.split('-', 1)
            try:
                n1, n2 = int(parts[0].strip()), int(parts[1].strip())
                if n1 < 1 or n2 > len(self.buffer) or n1 > n2:
                    print(f"Invalid range {n1}-{n2}.")
                    return
                del self.buffer[n1-1:n2]
                self.modified = True
                print(f"Deleted lines {n1}-{n2}.")
            except ValueError:
                print("Usage: DELETE <n1>-<n2>")
        else:
            try:
                n = int(arg)
                if n < 1 or n > len(self.buffer):
                    print(f"Line {n} is out of range.")
                    return
                del self.buffer[n-1]
                self.modified = True
                print(f"Deleted line {n}.")
            except ValueError:
                print("Usage: DELETE <n> or DELETE <n1>-<n2>")

    def _cmd_insert(self, arg: str):
        try:
            n = int(arg.strip())
        except ValueError:
            print("Usage: INSERT <n>")
            return
        if n < 1 or n > len(self.buffer) + 1:
            print(f"Line {n} is out of range.")
            return
        insert_pos = n - 1
        line_num = n
        while True:
            try:
                text = input(f"{line_num:4d}> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if text == '.':
                break
            self.buffer.insert(insert_pos, text)
            insert_pos += 1
            line_num += 1
            self.modified = True

    def _cmd_append(self, arg: str):
        line_num = len(self.buffer) + 1
        while True:
            try:
                text = input(f"{line_num:4d}> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if text == '.':
                break
            self.buffer.append(text)
            line_num += 1
            self.modified = True

    def _cmd_new(self, arg: str):
        if self.modified:
            if not self._confirm("Buffer has unsaved changes. Clear? (y/n) "):
                return
        self.buffer.clear()
        self.interpreter.reset()
        self.modified = False
        print("All cleared.")

    # ── execution commands ──

    def _cmd_run(self, arg: str):
        if not self.buffer:
            print("Buffer is empty. Nothing to run.")
            return
        source = '\n'.join(self.buffer)
        try:
            preprocessed = Preprocessor(source).process()
            tokens = Lexer(preprocessed).tokenize()
            ast = Parser(tokens).parse()

            self.interpreter.reset()
            self.interpreter.set_source_lines(self.buffer)
            ret = self.interpreter.execute_program(ast)
            print(f"Program exited with return value {ret}.")

        except StopExecution as e:
            print(f"Program exited with return value {e.code}.")
        except SmallCError as e:
            self._print_error(e, mode="run")
        except Exception as e:
            print(f"Internal error: {e}")

    def _cmd_check(self, arg: str):
        if not self.buffer:
            print("Buffer is empty.")
            return
        source = '\n'.join(self.buffer)
        try:
            preprocessed = Preprocessor(source).process()
            tokens = Lexer(preprocessed).tokenize()
            ast = Parser(tokens).parse()
            print("No errors found.")
        except SmallCError as e:
            self._print_error(e, mode="check")
            print("1 error(s) found.")

    def _cmd_trace(self, arg: str):
        upper = arg.upper().strip()
        if upper == 'ON':
            self.interpreter.trace_mode = True
            print("Trace mode enabled.")
        elif upper == 'OFF':
            self.interpreter.trace_mode = False
            print("Trace mode disabled.")
        else:
            print("Usage: TRACE ON | TRACE OFF")

    def _cmd_vars(self, arg: str):
        symbols = self.interpreter.get_global_vars()
        if not symbols:
            print("No variables defined.")
            return
        for name, sym in symbols:
            if sym.array_size is not None:
                # Show array contents
                vals = []
                for i in range(sym.array_size):
                    if sym.var_type == "int":
                        vals.append(str(self.interpreter.memory.read_int(
                            sym.address + i * 4)))
                    else:
                        vals.append(str(self.interpreter.memory.read_byte(
                            sym.address + i)))
                if len(vals) > 10:
                    display = ', '.join(vals[:10]) + ', ...'
                else:
                    display = ', '.join(vals)
                print(f"  {sym.var_type} {name}[{sym.array_size}] = {{{display}}}")
            elif sym.is_pointer:
                ptr_val = self.interpreter.memory.read_int(sym.address)
                print(f"  {sym.var_type} *{name} = {ptr_val}")
            elif sym.var_type == "char":
                val = self.interpreter.memory.read_byte(sym.address)
                if 32 <= val < 127:
                    print(f"  char {name} = {val} ('{chr(val)}')")
                else:
                    print(f"  char {name} = {val}")
            else:
                val = self.interpreter.memory.read_int(sym.address)
                print(f"  int {name} = {val}")

    def _cmd_funcs(self, arg: str):
        funcs = self.interpreter.get_functions()
        if funcs:
            for name, fdef in funcs.items():
                params_str = ', '.join(
                    f"{p.param_type}{' *' if p.is_pointer else ''}{' ' if not p.is_pointer else ''}{p.name}"
                    + ("[]" if p.is_array else "")
                    for p in fdef.params
                )
                ret = fdef.return_type.ljust(4)
                sig = f"{ret} {name}({params_str})"
                print(f"  {sig:<40s} line {fdef.line}")

        # Built-in functions
        print("  --- built-in functions ---")
        from .builtins import Builtins
        for fname, (ret, params) in Builtins.SIGNATURES.items():
            ret_s = ret.ljust(4)
            print(f"  {ret_s} {fname}({params}){' ' * max(1, 32 - len(fname) - len(params))}[built-in]")

    # ── system commands ──

    def _cmd_help(self, arg: str):
        arg = arg.strip().upper()
        if not arg:
            print("Available commands:")
            print("  LOAD <file>     - Load source file into buffer")
            print("  SAVE <file>     - Save buffer to file")
            print("  LIST [n|n1-n2]  - List buffer contents")
            print("  EDIT <n>        - Edit line n")
            print("  DELETE <n|n1-n2>- Delete line(s)")
            print("  INSERT <n>      - Insert lines before line n")
            print("  APPEND          - Append lines to end of buffer")
            print("  NEW             - Clear buffer and reset state")
            print("  RUN             - Execute the program in buffer")
            print("  CHECK           - Check syntax without executing")
            print("  TRACE ON|OFF    - Toggle execution tracing")
            print("  VARS            - Show global variables")
            print("  FUNCS           - Show defined functions")
            print("  HELP [command]  - Show help")
            print("  ABOUT           - Show version info")
            print("  CLEAR           - Clear screen")
            print("  QUIT / EXIT     - Exit interpreter")
            print()
            print("Or type Small-C code directly to execute it.")
        else:
            help_texts = {
                'LOAD': "LOAD <filename>\n  Load a Small-C source file into the program buffer.\n  Example: LOAD hello.sc",
                'SAVE': "SAVE <filename>\n  Save the current buffer to a file.\n  Example: SAVE myprogram.sc",
                'LIST': "LIST [n | n1-n2]\n  LIST       - Show all lines\n  LIST 5     - Show line 5\n  LIST 3-10  - Show lines 3 to 10",
                'RUN': "RUN\n  Execute the program in the buffer from main().",
                'CHECK': "CHECK\n  Check syntax of buffer contents without executing.",
                'TRACE': "TRACE ON | TRACE OFF\n  Toggle execution tracing. Shows each line as it executes.",
                'VARS': "VARS\n  Display all global variables with their current values.",
                'FUNCS': "FUNCS\n  List all user-defined and built-in functions.",
                'NEW': "NEW\n  Clear the buffer and reset all state.",
                'EDIT': "EDIT <n>\n  Edit line n. Press Enter without typing to keep original.",
                'DELETE': "DELETE <n> | DELETE <n1>-<n2>\n  Delete one or more lines from the buffer.",
                'INSERT': "INSERT <n>\n  Insert lines before line n. Type '.' on a line by itself to stop.",
                'APPEND': "APPEND\n  Add lines to the end of the buffer. Type '.' to stop.",
            }
            if arg in help_texts:
                print(help_texts[arg])
            else:
                print(f"No help available for '{arg}'.")

    def _cmd_about(self, arg: str):
        print(f"Small-C Interactive Interpreter v{__version__}")
        print(f"Author: {__author__}")
        print(f"System Software Final Project, {__semester__}")

    def _cmd_clear(self, arg: str):
        os.system('cls' if os.name == 'nt' else 'clear')

    def _cmd_quit(self, arg: str):
        if self.modified:
            if not self._confirm("Buffer has unsaved changes. Quit anyway? (y/n) "):
                return
        print("Goodbye.")
        sys.exit(0)

    # ── interactive execution ──

    def _execute_interactive(self, code: str):
        """Parse and execute code entered at the prompt."""
        try:
            preprocessed = Preprocessor(code).process()
            tokens = Lexer(preprocessed).tokenize()
            ast = Parser(tokens).parse()
            self.interpreter.execute_interactive(ast)
        except StopExecution:
            pass
        except SmallCError as e:
            self._print_error(e, mode="interactive")

    # ── error formatting ──

    def _print_error(self, e: SmallCError, mode: str = "interactive"):
        """Format error messages matching the assignment spec.
        mode: 'interactive' (sc> prompt), 'run' (RUN command), 'check' (CHECK command)
        """
        from .errors import ParseError, LexerError, RuntimeError_
        msg = e.message if hasattr(e, 'message') else str(e)

        if isinstance(e, (ParseError, LexerError)):
            if mode in ("run", "check") and e.line > 0:
                print(f"Error at line {e.line}: {msg}.")
            else:
                print(f"Syntax error: {msg}.")
        elif isinstance(e, RuntimeError_):
            if mode in ("run", "check") and e.line > 0:
                print(f"Runtime error at line {e.line}: {msg}.")
            else:
                print(f"Runtime error: {msg}.")
        else:
            if e.line > 0:
                print(f"Error at line {e.line}: {msg}.")
            else:
                print(f"Error: {msg}.")

    # ── utilities ──

    def _confirm(self, prompt: str) -> bool:
        try:
            ans = input(prompt).strip().lower()
            return ans in ('y', 'yes')
        except (EOFError, KeyboardInterrupt):
            print()
            return False

    def _print_banner(self):
        print("==============================================")
        print(f"  Small-C Interactive Interpreter v{__version__}")
        print(f"  System Software Final Project, {__semester__}")
        print("==============================================")
        print("Type 'HELP' for a list of commands.")
        print()
