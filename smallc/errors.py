"""Exception hierarchy for the Small-C interpreter."""


class SmallCError(Exception):
    """Base exception for all Small-C errors."""
    def __init__(self, message: str, line: int = 0, col: int = 0):
        self.message = message
        self.line = line
        self.col = col
        if line > 0:
            super().__init__(f"line {line}: {message}")
        else:
            super().__init__(message)


class LexerError(SmallCError):
    """Error during lexical analysis."""
    pass


class ParseError(SmallCError):
    """Error during parsing."""
    pass


class RuntimeError_(SmallCError):
    """Error during interpretation/execution."""
    pass


class StopExecution(Exception):
    """Raised when exit() is called or user stops execution."""
    def __init__(self, code: int = 0):
        self.code = code
        super().__init__()


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class ReturnSignal(Exception):
    def __init__(self, value=None):
        self.value = value
        super().__init__()
