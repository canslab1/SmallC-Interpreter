"""Tree-walking interpreter for Small-C."""

from .ast_nodes import *
from .errors import RuntimeError_, StopExecution, BreakSignal, ContinueSignal, ReturnSignal
from .memory import Memory, INT_SIZE, CHAR_SIZE
from .symtable import Symbol, Environment
from .builtins import Builtins


class Interpreter:
    """Executes a Small-C AST via tree-walking evaluation."""

    def __init__(self):
        self.memory = Memory()
        self.global_env = Environment(name="global")
        self.current_env = self.global_env
        self.functions: dict[str, FunctionDef] = {}
        self.trace_mode: bool = False
        self.source_lines: list[str] = []

        self._call_depth: int = 0
        self._output = print
        self._input = input

        self.builtins = Builtins(self.memory, self._do_output, self._do_input)

    # ── output / input indirection ──────────────────────────────────────────

    def _do_output(self, text: str):
        self._output(text)

    def _do_input(self) -> str:
        return self._input()

    # ── lifecycle ────────────────────────────────────────────────────────────

    def reset(self):
        """Reset interpreter state for a fresh run."""
        self.memory.reset()
        self.global_env = Environment(name="global")
        self.current_env = self.global_env
        self.functions.clear()
        self._call_depth = 0
        self.builtins = Builtins(self.memory, self._do_output, self._do_input)

    def set_source_lines(self, lines: list[str]):
        """Store source lines for TRACE display."""
        self.source_lines = lines

    # ── public entry points ─────────────────────────────────────────────────

    def execute_program(self, ast: Program) -> int:
        """Register top-level declarations, then call main(). Returns main's return value."""
        for decl in ast.declarations:
            if isinstance(decl, FunctionDef):
                self.functions[decl.name] = decl
            elif isinstance(decl, VarDeclaration):
                self._visit_VarDeclaration(decl)
            else:
                self._visit(decl)

        if "main" not in self.functions:
            raise RuntimeError_("program has no main() function")

        return self._to_int(self._call_function("main", []))

    def execute_interactive(self, ast):
        """Execute a single statement or declaration in global scope (REPL)."""
        if isinstance(ast, Program):
            for decl in ast.declarations:
                if isinstance(decl, FunctionDef):
                    self.functions[decl.name] = decl
                else:
                    self._visit(decl)
        else:
            self._visit(ast)

    # ── query helpers for REPL commands ──────────────────────────────────────

    def get_global_vars(self) -> list[tuple[str, Symbol]]:
        """Return list of (name, Symbol) from the global environment."""
        return self.global_env.all_symbols()

    def get_functions(self) -> dict[str, FunctionDef]:
        """Return the user-defined functions dict."""
        return self.functions

    # ── visitor dispatch ────────────────────────────────────────────────────

    def _visit(self, node):
        if node is None:
            return 0
        method_name = f"_visit_{type(node).__name__}"
        visitor = getattr(self, method_name, None)
        if visitor is None:
            raise RuntimeError_(
                f"no visitor for {type(node).__name__}", node.line, node.col
            )
        return visitor(node)

    # ── trace helper ────────────────────────────────────────────────────────

    def _trace(self, node):
        """If trace mode is on, print the source line being executed."""
        if not self.trace_mode:
            return
        if not self.source_lines:
            return
        line = getattr(node, 'line', 0)
        if line <= 0 or line > len(self.source_lines):
            return
        indent = "  " * self._call_depth
        content = self.source_lines[line - 1].rstrip()
        self._output(f"{indent}[line {line:3d}] {content.strip()}\n")

    # ── declarations ────────────────────────────────────────────────────────

    def _visit_Program(self, node: Program):
        for decl in node.declarations:
            self._visit(decl)

    def _visit_FunctionDef(self, node: FunctionDef):
        self.functions[node.name] = node

    def _visit_VarDeclaration(self, node: VarDeclaration):
        self._trace(node)

        if node.array_size is not None:
            # Array declaration: allocate N * elem_size bytes
            elem_size = INT_SIZE if node.var_type == "int" else CHAR_SIZE
            total = node.array_size * elem_size
            addr = self.memory.alloc_var(total)
            sym = Symbol(
                name=node.name,
                var_type=node.var_type,
                is_pointer=False,
                array_size=node.array_size,
                address=addr,
                value=addr,
            )
            # Handle initializer
            if node.initializer is not None:
                if isinstance(node.initializer, ArrayInitList):
                    for i, elem_node in enumerate(node.initializer.elements):
                        val = self._to_int(self._visit(elem_node))
                        if node.var_type == "int":
                            self.memory.write_int(addr + i * INT_SIZE, val)
                        else:
                            self.memory.write_byte(addr + i * CHAR_SIZE, val)
                elif isinstance(node.initializer, StringLiteral):
                    # char arr[] = "hello";
                    s = node.initializer.value
                    for i, ch in enumerate(s):
                        self.memory.write_byte(addr + i, ord(ch))
                    self.memory.write_byte(addr + len(s), 0)
            self.current_env.declare(sym)

        elif node.is_pointer:
            # Pointer declaration: allocate 4 bytes for the pointer itself
            addr = self.memory.alloc_var(INT_SIZE)
            val = 0
            if node.initializer is not None:
                val = self._to_int(self._visit(node.initializer))
            self.memory.write_int(addr, val)
            sym = Symbol(
                name=node.name,
                var_type=node.var_type,
                is_pointer=True,
                address=addr,
                value=val,
            )
            self.current_env.declare(sym)

        else:
            # Scalar variable: allocate 4 bytes (int) or 1 byte (char)
            elem_size = INT_SIZE if node.var_type == "int" else CHAR_SIZE
            addr = self.memory.alloc_var(elem_size)
            val = 0
            if node.initializer is not None:
                raw = self._visit(node.initializer)
                if isinstance(raw, str) and len(raw) == 1 and node.var_type == "char":
                    val = ord(raw)
                else:
                    val = self._to_int(raw)
            if node.var_type == "int":
                self.memory.write_int(addr, val)
            else:
                self.memory.write_byte(addr, val)
            sym = Symbol(
                name=node.name,
                var_type=node.var_type,
                address=addr,
                value=val,
            )
            self.current_env.declare(sym)

    # ── statements ──────────────────────────────────────────────────────────

    def _visit_Block(self, node: Block):
        # Create a new scope for the block
        prev_env = self.current_env
        self.current_env = Environment(parent=prev_env, name="block")
        try:
            for stmt in node.statements:
                self._visit(stmt)
        finally:
            self.current_env = prev_env

    def _visit_ExpressionStatement(self, node: ExpressionStatement):
        self._trace(node)
        if node.expr is not None:
            return self._visit(node.expr)
        return 0

    def _visit_IfStatement(self, node: IfStatement):
        self._trace(node)
        cond = self._to_int(self._visit(node.condition))
        if cond:
            self._visit(node.then_branch)
        elif node.else_branch is not None:
            self._visit(node.else_branch)

    def _visit_WhileLoop(self, node: WhileLoop):
        while True:
            self._trace(node)
            cond = self._to_int(self._visit(node.condition))
            if not cond:
                break
            try:
                self._visit(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                continue

    def _visit_DoWhileLoop(self, node: DoWhileLoop):
        while True:
            self._trace(node)
            try:
                self._visit(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            cond = self._to_int(self._visit(node.condition))
            if not cond:
                break

    def _visit_ForLoop(self, node: ForLoop):
        if node.init is not None:
            self._visit(node.init)
        while True:
            self._trace(node)
            if node.condition is not None:
                cond = self._to_int(self._visit(node.condition))
                if not cond:
                    break
            try:
                self._visit(node.body)
            except BreakSignal:
                break
            except ContinueSignal:
                pass
            if node.update is not None:
                self._visit(node.update)

    def _visit_SwitchStatement(self, node: SwitchStatement):
        self._trace(node)
        val = self._to_int(self._visit(node.expr))
        matched = False
        fell_through = False

        for case in node.cases:
            case_val = self._to_int(self._visit(case.value))
            if fell_through or case_val == val:
                matched = True
                try:
                    for stmt in case.body:
                        self._visit(stmt)
                    fell_through = True
                except BreakSignal:
                    return

        if not matched and node.default is not None:
            if isinstance(node.default, list):
                try:
                    for stmt in node.default:
                        self._visit(stmt)
                except BreakSignal:
                    return
            else:
                try:
                    self._visit(node.default)
                except BreakSignal:
                    return

    def _visit_CaseClause(self, node: CaseClause):
        # Handled by SwitchStatement directly
        pass

    def _visit_ReturnStatement(self, node: ReturnStatement):
        self._trace(node)
        value = None
        if node.value is not None:
            value = self._visit(node.value)
        raise ReturnSignal(value)

    def _visit_BreakStatement(self, node: BreakStatement):
        self._trace(node)
        raise BreakSignal()

    def _visit_ContinueStatement(self, node: ContinueStatement):
        self._trace(node)
        raise ContinueSignal()

    # ── expressions ─────────────────────────────────────────────────────────

    def _visit_IntLiteral(self, node: IntLiteral):
        return node.value

    def _visit_CharLiteral(self, node: CharLiteral):
        return ord(node.value) if node.value else 0

    def _visit_StringLiteral(self, node: StringLiteral):
        addr = self.memory.store_string(node.value)
        return addr

    def _visit_Identifier(self, node: Identifier):
        sym = self.current_env.get(node.name)
        if sym.array_size is not None:
            # Array name decays to pointer (base address)
            return sym.address
        if sym.is_pointer:
            # Read the pointer value from memory
            return self.memory.read_int(sym.address)
        # Scalar: read from memory
        if sym.var_type == "int":
            return self.memory.read_int(sym.address)
        else:
            return self.memory.read_byte(sym.address)

    def _visit_BinaryOp(self, node: BinaryOp):
        left = self._to_int(self._visit(node.left))

        # Short-circuit for logical operators
        if node.op == '&&':
            if not left:
                return 0
            return 1 if self._to_int(self._visit(node.right)) else 0
        if node.op == '||':
            if left:
                return 1
            return 1 if self._to_int(self._visit(node.right)) else 0

        right = self._to_int(self._visit(node.right))

        if node.op == '+':
            return left + right
        if node.op == '-':
            return left - right
        if node.op == '*':
            return left * right
        if node.op == '/':
            if right == 0:
                raise RuntimeError_("division by zero", node.line, node.col)
            # C-style truncation toward zero
            sign = -1 if (left < 0) != (right < 0) else 1
            return sign * (abs(left) // abs(right))
        if node.op == '%':
            if right == 0:
                raise RuntimeError_("division by zero", node.line, node.col)
            # C-style: result has same sign as dividend
            return left - (left // right) * right if right != 0 else 0
        if node.op == '==':
            return int(left == right)
        if node.op == '!=':
            return int(left != right)
        if node.op == '<':
            return int(left < right)
        if node.op == '>':
            return int(left > right)
        if node.op == '<=':
            return int(left <= right)
        if node.op == '>=':
            return int(left >= right)
        if node.op == '&':
            return left & right
        if node.op == '|':
            return left | right
        if node.op == '^':
            return left ^ right
        if node.op == '<<':
            return left << right
        if node.op == '>>':
            return left >> right

        raise RuntimeError_(f"unknown operator: {node.op}", node.line, node.col)

    def _visit_UnaryOp(self, node: UnaryOp):
        if node.op == '&':
            # Address-of operator
            return self._address_of(node.operand, node)

        if node.op == '*':
            # Pointer dereference
            addr = self._to_int(self._visit(node.operand))
            # Determine the type for proper read size
            if isinstance(node.operand, Identifier):
                sym = self.current_env.get(node.operand.name)
                if sym.var_type == "char":
                    return self.memory.read_byte(addr)
            return self.memory.read_int(addr)

        if node.op == '++':
            # Prefix increment
            old_val = self._to_int(self._visit(node.operand))
            new_val = old_val + 1
            self._assign_to(node.operand, new_val)
            return new_val

        if node.op == '--':
            # Prefix decrement
            old_val = self._to_int(self._visit(node.operand))
            new_val = old_val - 1
            self._assign_to(node.operand, new_val)
            return new_val

        operand = self._to_int(self._visit(node.operand))

        if node.op == '-':
            return -operand
        if node.op == '+':
            return operand
        if node.op == '!':
            return int(not operand)
        if node.op == '~':
            return ~operand

        raise RuntimeError_(f"unknown unary operator: {node.op}", node.line, node.col)

    def _address_of(self, operand, parent_node):
        """Compute the address of an lvalue expression."""
        if isinstance(operand, Identifier):
            sym = self.current_env.get(operand.name)
            return sym.address

        if isinstance(operand, ArrayAccess):
            # &arr[i] -> base + i * elem_size
            if isinstance(operand.array, Identifier):
                sym = self.current_env.get(operand.array.name)
                idx = self._to_int(self._visit(operand.index))
                if sym.array_size is not None:
                    base = sym.address
                else:
                    base = self.memory.read_int(sym.address)
                elem_size = INT_SIZE if sym.var_type == "int" else CHAR_SIZE
                return base + idx * elem_size
            # Generic pointer[i]
            base = self._to_int(self._visit(operand.array))
            idx = self._to_int(self._visit(operand.index))
            return base + idx * INT_SIZE

        if isinstance(operand, UnaryOp) and operand.op == '*':
            # &(*ptr) == ptr
            return self._to_int(self._visit(operand.operand))

        raise RuntimeError_(
            "cannot take address of expression",
            parent_node.line, parent_node.col
        )

    def _visit_PostfixOp(self, node: PostfixOp):
        old_val = self._to_int(self._visit(node.operand))
        if node.op == '++':
            self._assign_to(node.operand, old_val + 1)
        elif node.op == '--':
            self._assign_to(node.operand, old_val - 1)
        return old_val  # postfix returns the original value

    def _visit_Assignment(self, node: Assignment):
        right = self._visit(node.value)

        if node.op == '=':
            val = right
        else:
            left = self._to_int(self._visit(node.target))
            right_int = self._to_int(right)
            if node.op == '+=':
                val = left + right_int
            elif node.op == '-=':
                val = left - right_int
            elif node.op == '*=':
                val = left * right_int
            elif node.op == '/=':
                if right_int == 0:
                    raise RuntimeError_("division by zero", node.line, node.col)
                sign = -1 if (left < 0) != (right_int < 0) else 1
                val = sign * (abs(left) // abs(right_int))
            elif node.op == '%=':
                if right_int == 0:
                    raise RuntimeError_("division by zero", node.line, node.col)
                val = left - (left // right_int) * right_int
            elif node.op == '&=':
                val = left & right_int
            elif node.op == '|=':
                val = left | right_int
            elif node.op == '^=':
                val = left ^ right_int
            elif node.op == '<<=':
                val = left << right_int
            elif node.op == '>>=':
                val = left >> right_int
            else:
                raise RuntimeError_(
                    f"unknown assignment operator: {node.op}", node.line, node.col
                )

        self._assign_to(node.target, val)
        return self._to_int(val)

    def _visit_FunctionCall(self, node: FunctionCall):
        args = [self._visit(arg) for arg in node.arguments]

        # Check built-in functions first
        if self.builtins.has(node.name):
            return self.builtins.call(node.name, args)

        # User-defined function
        return self._call_function(node.name, args)

    def _visit_ArrayAccess(self, node: ArrayAccess):
        idx = self._to_int(self._visit(node.index))

        if isinstance(node.array, Identifier):
            sym = self.current_env.get(node.array.name)

            # Bounds checking
            if sym.array_size is not None:
                if idx < 0 or idx >= sym.array_size:
                    raise RuntimeError_(
                        f"array index out of bounds (index {idx}, size {sym.array_size})",
                        node.line, node.col
                    )

            if sym.array_size is not None:
                base = sym.address
            else:
                # Pointer: read the pointer value to get the base address
                base = self.memory.read_int(sym.address)

            elem_size = INT_SIZE if sym.var_type == "int" else CHAR_SIZE
            target_addr = base + idx * elem_size
            if sym.var_type == "int":
                return self.memory.read_int(target_addr)
            else:
                return self.memory.read_byte(target_addr)

        # Generic expression used as array (e.g. ptr[i])
        base = self._to_int(self._visit(node.array))
        target_addr = base + idx * INT_SIZE
        return self.memory.read_int(target_addr)

    def _visit_CastExpr(self, node: CastExpr):
        val = self._to_int(self._visit(node.expr))
        if node.target_type == "char":
            return val & 0xFF
        return val

    def _visit_ArrayInitList(self, node: ArrayInitList):
        # This is typically handled inline by VarDeclaration.
        # If visited standalone, evaluate and return the list of values.
        return [self._visit(elem) for elem in node.elements]

    # ── function call machinery ─────────────────────────────────────────────

    def _call_function(self, name: str, args: list):
        if name not in self.functions:
            raise RuntimeError_(f"undefined function: '{name}'")

        func = self.functions[name]

        # Create a new environment with parent = global (C scoping)
        prev_env = self.current_env
        func_env = Environment(parent=self.global_env, name=f"func:{name}")
        self.current_env = func_env
        self._call_depth += 1

        try:
            # Bind parameters
            for i, param in enumerate(func.params):
                raw_val = args[i] if i < len(args) else 0

                if param.is_pointer or param.is_array:
                    # Pointer/array params: the value IS the address
                    addr = self.memory.alloc_var(INT_SIZE)
                    int_val = self._to_int(raw_val)
                    self.memory.write_int(addr, int_val)
                    sym = Symbol(
                        name=param.name,
                        var_type=param.param_type,
                        is_pointer=True,
                        address=addr,
                        value=int_val,
                    )
                    func_env.declare(sym)
                else:
                    # Value parameter: copy the value
                    if isinstance(raw_val, str):
                        int_val = ord(raw_val[0]) if raw_val else 0
                    else:
                        int_val = self._to_int(raw_val)

                    elem_size = INT_SIZE if param.param_type == "int" else CHAR_SIZE
                    addr = self.memory.alloc_var(elem_size)
                    if param.param_type == "int":
                        self.memory.write_int(addr, int_val)
                    else:
                        self.memory.write_byte(addr, int_val)
                    sym = Symbol(
                        name=param.name,
                        var_type=param.param_type,
                        address=addr,
                        value=int_val,
                    )
                    func_env.declare(sym)

            # Execute function body
            result = 0
            try:
                self._visit(func.body)
            except ReturnSignal as ret:
                result = self._to_int(ret.value) if ret.value is not None else 0

            return result
        finally:
            self._call_depth -= 1
            self.current_env = prev_env

    # ── assignment helper ───────────────────────────────────────────────────

    def _assign_to(self, target_node, value):
        """Assign a value to an lvalue: Identifier, ArrayAccess, or *ptr."""
        int_val = self._to_int(value)

        if isinstance(target_node, Identifier):
            sym = self.current_env.get(target_node.name)
            if sym.is_pointer:
                self.memory.write_int(sym.address, int_val)
            elif sym.var_type == "int":
                self.memory.write_int(sym.address, int_val)
            else:
                self.memory.write_byte(sym.address, int_val)
            sym.value = int_val
            return

        if isinstance(target_node, ArrayAccess):
            idx = self._to_int(self._visit(target_node.index))

            if isinstance(target_node.array, Identifier):
                sym = self.current_env.get(target_node.array.name)

                # Bounds checking
                if sym.array_size is not None:
                    if idx < 0 or idx >= sym.array_size:
                        raise RuntimeError_(
                            f"array index out of bounds (index {idx}, size {sym.array_size})",
                            target_node.line, target_node.col
                        )

                if sym.array_size is not None:
                    base = sym.address
                else:
                    base = self.memory.read_int(sym.address)

                elem_size = INT_SIZE if sym.var_type == "int" else CHAR_SIZE
                target_addr = base + idx * elem_size
                if sym.var_type == "int":
                    self.memory.write_int(target_addr, int_val)
                else:
                    self.memory.write_byte(target_addr, int_val)
            else:
                base = self._to_int(self._visit(target_node.array))
                target_addr = base + idx * INT_SIZE
                self.memory.write_int(target_addr, int_val)
            return

        if isinstance(target_node, UnaryOp) and target_node.op == '*':
            # Dereference assignment: *ptr = value
            addr = self._to_int(self._visit(target_node.operand))
            # Try to determine the pointed-to type
            if isinstance(target_node.operand, Identifier):
                sym = self.current_env.get(target_node.operand.name)
                if sym.var_type == "char":
                    self.memory.write_byte(addr, int_val)
                    return
            self.memory.write_int(addr, int_val)
            return

        raise RuntimeError_(
            "invalid assignment target",
            getattr(target_node, 'line', 0),
            getattr(target_node, 'col', 0),
        )

    # ── utilities ───────────────────────────────────────────────────────────

    def _to_int(self, value) -> int:
        """Convert a value to an integer."""
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            return ord(value[0]) if value else 0
        if isinstance(value, bool):
            return int(value)
        if value is None:
            return 0
        if isinstance(value, float):
            return int(value)
        if isinstance(value, list):
            return len(value)
        return int(value)
