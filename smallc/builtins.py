"""All 23 built-in functions for Small-C, matching the assignment spec."""

import math
import random
from typing import Callable

from .errors import RuntimeError_
from .memory import Memory


class Builtins:
    """Implements all built-in library functions."""

    # Metadata for FUNCS display: (return_type, signature)
    SIGNATURES = {
        "putchar":    ("int",  "int ch"),
        "getchar":    ("int",  ""),
        "printf":     ("void", "char *fmt, ..."),
        "puts":       ("void", "char *s"),
        "scanf":      ("int",  "char *fmt, ..."),
        "strlen":     ("int",  "char *s"),
        "strcpy":     ("void", "char *dest, char *src"),
        "strcmp":      ("int",  "char *s1, char *s2"),
        "strcat":     ("void", "char *dest, char *src"),
        "abs":        ("int",  "int x"),
        "max":        ("int",  "int a, int b"),
        "min":        ("int",  "int a, int b"),
        "pow":        ("int",  "int base, int exp"),
        "sqrt":       ("int",  "int x"),
        "mod":        ("int",  "int a, int b"),
        "rand":       ("int",  ""),
        "srand":      ("void", "int seed"),
        "memset":     ("void", "char *ptr, int value, int size"),
        "sizeof_int": ("int",  ""),
        "sizeof_char":("int",  ""),
        "atoi":       ("int",  "char *s"),
        "itoa":       ("void", "int value, char *str"),
        "exit":       ("void", "int code"),
    }

    def __init__(self, mem: Memory,
                 output_fn: Callable[[str], None],
                 input_fn: Callable[[], str]):
        self.mem = mem
        self._out = output_fn
        self._in = input_fn
        self._rng = random.Random(0)

    def has(self, name: str) -> bool:
        return name in self.SIGNATURES

    def call(self, name: str, args: list[int]) -> int:
        fn = getattr(self, f'_f_{name}', None)
        if fn is None:
            raise RuntimeError_(f"undefined function: '{name}'")
        return fn(args)

    # ── I/O ──

    def _f_putchar(self, a):
        ch = a[0] & 0x7F
        self._out(chr(ch))
        return ch

    def _f_getchar(self, a):
        s = self._in()
        return ord(s[0]) if s else -1

    def _f_printf(self, a):
        if not a:
            return 0
        fmt = a[0]
        if isinstance(fmt, int):
            fmt = self.mem.read_string(fmt)
        ai = 1
        out = []
        i = 0
        while i < len(fmt):
            if fmt[i] == '%':
                i += 1
                if i >= len(fmt):
                    break
                spec = fmt[i]
                if spec == 'd' or spec == 'i':
                    v = self._signed(a[ai]) if ai < len(a) else 0
                    out.append(str(v)); ai += 1
                elif spec == 'c':
                    v = a[ai] if ai < len(a) else 0
                    out.append(chr(v & 0x7F)); ai += 1
                elif spec == 's':
                    v = a[ai] if ai < len(a) else 0
                    out.append(self.mem.read_string(v) if isinstance(v, int) else str(v))
                    ai += 1
                elif spec == 'x':
                    v = a[ai] if ai < len(a) else 0
                    out.append(format(v & 0xFFFFFFFF, 'x')); ai += 1
                elif spec == '%':
                    out.append('%')
                else:
                    out.append('%' + spec)
            else:
                out.append(fmt[i])
            i += 1
        s = ''.join(out)
        self._out(s)
        return len(s)

    def _f_puts(self, a):
        s = a[0]
        if isinstance(s, int):
            s = self.mem.read_string(s)
        self._out(str(s) + '\n')
        return 0

    def _f_scanf(self, a):
        if len(a) < 2:
            raise RuntimeError_("scanf: expected format string and address arguments")
        fmt = a[0]
        if isinstance(fmt, int):
            fmt = self.mem.read_string(fmt)
        text = self._in()
        if not text:
            return 0
        ai = 1; ti = 0; count = 0; i = 0
        while i < len(fmt) and ai < len(a):
            if fmt[i] == '%':
                i += 1
                if i >= len(fmt):
                    break
                while ti < len(text) and text[ti] in (' ', '\t'):
                    ti += 1
                if fmt[i] == 'd':
                    ns = ""
                    if ti < len(text) and text[ti] in '+-':
                        ns += text[ti]; ti += 1
                    while ti < len(text) and text[ti].isdigit():
                        ns += text[ti]; ti += 1
                    if ns and ns not in '+-':
                        self.mem.write_int(a[ai], int(ns)); count += 1
                    ai += 1
                elif fmt[i] == 'c':
                    if ti < len(text):
                        self.mem.write_byte(a[ai], ord(text[ti])); ti += 1; count += 1
                    ai += 1
                i += 1
            else:
                i += 1; ti += 1
        return count

    # ── String ──

    def _f_strlen(self, a):
        return len(self.mem.read_string(a[0]))

    def _f_strcpy(self, a):
        dest, src = a[0], a[1]
        s = self.mem.read_string(src)
        for i, ch in enumerate(s):
            self.mem.write_byte(dest + i, ord(ch))
        self.mem.write_byte(dest + len(s), 0)
        return 0

    def _f_strcmp(self, a):
        s1 = self.mem.read_string(a[0])
        s2 = self.mem.read_string(a[1])
        if s1 < s2: return -1
        if s1 > s2: return 1
        return 0

    def _f_strcat(self, a):
        dest, src = a[0], a[1]
        d = self.mem.read_string(dest)
        s = self.mem.read_string(src)
        offset = len(d)
        for i, ch in enumerate(s):
            self.mem.write_byte(dest + offset + i, ord(ch))
        self.mem.write_byte(dest + offset + len(s), 0)
        return 0

    # ── Math ──

    def _f_abs(self, a):
        v = self._signed(a[0])
        return v if v >= 0 else -v

    def _f_max(self, a):
        return max(self._signed(a[0]), self._signed(a[1]))

    def _f_min(self, a):
        return min(self._signed(a[0]), self._signed(a[1]))

    def _f_pow(self, a):
        base = self._signed(a[0])
        exp = self._signed(a[1])
        if exp < 0:
            return 0
        if exp == 0:
            return 1
        return int(base ** exp)

    def _f_sqrt(self, a):
        v = self._signed(a[0])
        if v < 0:
            raise RuntimeError_("sqrt() argument must be non-negative")
        return int(math.isqrt(v))

    def _f_mod(self, a):
        b = self._signed(a[1])
        if b == 0:
            raise RuntimeError_("mod() division by zero")
        return self._signed(a[0]) % b

    def _f_rand(self, a):
        return self._rng.randint(0, 32767)

    def _f_srand(self, a):
        self._rng.seed(a[0])
        return 0

    # ── Memory & utility ──

    def _f_memset(self, a):
        ptr, val, size = a[0], a[1] & 0xFF, a[2]
        for i in range(size):
            self.mem.write_byte(ptr + i, val)
        return 0

    def _f_sizeof_int(self, a):
        return 4

    def _f_sizeof_char(self, a):
        return 1

    def _f_atoi(self, a):
        s = self.mem.read_string(a[0])
        s = s.strip()
        if not s:
            return 0
        try:
            return int(s)
        except ValueError:
            # try to read leading digits
            ns = ""
            i = 0
            if i < len(s) and s[i] in '+-':
                ns += s[i]; i += 1
            while i < len(s) and s[i].isdigit():
                ns += s[i]; i += 1
            return int(ns) if ns and ns not in '+-' else 0

    def _f_itoa(self, a):
        val = self._signed(a[0])
        addr = a[1]
        s = str(val)
        for i, ch in enumerate(s):
            self.mem.write_byte(addr + i, ord(ch))
        self.mem.write_byte(addr + len(s), 0)
        return 0

    def _f_exit(self, a):
        from .errors import StopExecution
        raise StopExecution(a[0] if a else 0)

    def _signed(self, v: int) -> int:
        """Convert to signed 32-bit."""
        v = v & 0xFFFFFFFF
        return v if v < 0x80000000 else v - 0x100000000
