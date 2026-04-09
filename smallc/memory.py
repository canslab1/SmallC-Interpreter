"""Simulated flat memory for arrays, pointers and strings."""

from .errors import RuntimeError_

# Memory layout:
#   0x0000 - 0x03FF : reserved (null zone)
#   0x0400 (1024)   : start of variable storage
#   0x8000 (32768)  : start of heap (malloc)
#   Total size: 65536 bytes

MEM_SIZE = 65536
VAR_BASE = 1024
HEAP_BASE = 32768

INT_SIZE = 4
CHAR_SIZE = 1


class Memory:
    """Byte-addressable simulated memory."""

    def __init__(self):
        self.data = bytearray(MEM_SIZE)
        self._var_next = VAR_BASE
        self._heap_next = HEAP_BASE
        self._allocs: dict[int, int] = {}  # addr -> size

    def reset(self):
        self.data = bytearray(MEM_SIZE)
        self._var_next = VAR_BASE
        self._heap_next = HEAP_BASE
        self._allocs.clear()

    # ── variable storage allocation ──

    def alloc_var(self, size: int) -> int:
        """Allocate space in the variable region. Returns address."""
        addr = self._var_next
        self._var_next += size
        # align to 4
        if self._var_next % 4:
            self._var_next += 4 - (self._var_next % 4)
        if self._var_next >= HEAP_BASE:
            raise RuntimeError_("stack overflow: variable storage exhausted")
        return addr

    # ── heap (malloc/free) ──

    def malloc(self, size: int) -> int:
        if size <= 0:
            return 0
        addr = self._heap_next
        if addr + size > MEM_SIZE:
            raise RuntimeError_("out of memory: heap exhausted")
        self._allocs[addr] = size
        self._heap_next += size
        if self._heap_next % 4:
            self._heap_next += 4 - (self._heap_next % 4)
        return addr

    def free(self, addr: int):
        self._allocs.pop(addr, None)

    # ── read / write ──

    def _check(self, addr: int, size: int):
        if addr < 0 or addr + size > MEM_SIZE:
            raise RuntimeError_(f"memory access out of bounds: address {addr}")

    def read_byte(self, addr: int) -> int:
        self._check(addr, 1)
        v = self.data[addr]
        return v if v < 128 else v - 256  # signed char

    def write_byte(self, addr: int, value: int):
        self._check(addr, 1)
        self.data[addr] = value & 0xFF

    def read_int(self, addr: int) -> int:
        self._check(addr, 4)
        return int.from_bytes(self.data[addr:addr+4], 'little', signed=True)

    def write_int(self, addr: int, value: int):
        self._check(addr, 4)
        self.data[addr:addr+4] = (value & 0xFFFFFFFF).to_bytes(4, 'little')

    def store_string(self, s: str) -> int:
        encoded = s.encode('ascii', errors='replace') + b'\0'
        addr = self.alloc_var(len(encoded))
        for i, b in enumerate(encoded):
            self.data[addr + i] = b
        return addr

    def read_string(self, addr: int) -> str:
        self._check(addr, 1)
        chars = []
        while 0 <= addr < MEM_SIZE:
            b = self.data[addr]
            if b == 0:
                break
            chars.append(chr(b))
            addr += 1
        return ''.join(chars)
