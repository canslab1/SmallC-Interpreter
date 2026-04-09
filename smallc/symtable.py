"""Symbol table / environment with scope chain."""

from .errors import RuntimeError_
from .memory import INT_SIZE, CHAR_SIZE


class Symbol:
    """A variable entry in the symbol table."""
    __slots__ = ('name', 'var_type', 'is_pointer', 'array_size', 'address', 'value')

    def __init__(self, name: str, var_type: str, is_pointer: bool = False,
                 array_size: int | None = None, address: int | None = None,
                 value: int = 0):
        self.name = name
        self.var_type = var_type       # "int" or "char"
        self.is_pointer = is_pointer
        self.array_size = array_size   # None for non-array
        self.address = address         # memory address for arrays / addressable vars
        self.value = value             # current value (int)

    @property
    def elem_size(self) -> int:
        return INT_SIZE if self.var_type == "int" else CHAR_SIZE


class Environment:
    """Lexical scope chain."""

    def __init__(self, parent: 'Environment | None' = None, name: str = "global"):
        self.parent = parent
        self.name = name
        self.symbols: dict[str, Symbol] = {}

    def declare(self, sym: Symbol):
        if sym.name in self.symbols:
            raise RuntimeError_(f"variable '{sym.name}' already declared in this scope")
        self.symbols[sym.name] = sym

    def get(self, name: str) -> Symbol:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.get(name)
        raise RuntimeError_(f"undefined variable: '{name}'")

    def has(self, name: str) -> bool:
        if name in self.symbols:
            return True
        return self.parent.has(name) if self.parent else False

    def set_value(self, name: str, value: int):
        if name in self.symbols:
            self.symbols[name].value = value
            return
        if self.parent:
            self.parent.set_value(name, value)
            return
        raise RuntimeError_(f"undefined variable: '{name}'")

    def all_symbols(self) -> list[tuple[str, Symbol]]:
        """Return all symbols from this scope (not parent), for VARS display."""
        return list(self.symbols.items())
