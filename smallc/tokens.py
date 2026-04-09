"""Token types and Token dataclass for the Small-C lexer."""

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    # Literals
    INT_LITERAL = auto()
    CHAR_LITERAL = auto()
    STRING_LITERAL = auto()
    IDENTIFIER = auto()

    # Type keywords
    INT = auto()
    CHAR = auto()
    VOID = auto()

    # Control flow keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    FOR = auto()
    DO = auto()
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()
    BREAK = auto()
    CONTINUE = auto()
    RETURN = auto()

    # Arithmetic operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    # Comparison operators
    EQ = auto()
    NEQ = auto()
    LT = auto()
    GT = auto()
    LTE = auto()
    GTE = auto()

    # Logical operators
    AND = auto()
    OR = auto()
    NOT = auto()

    # Bitwise operators
    AMP = auto()
    PIPE = auto()
    CARET = auto()
    TILDE = auto()
    LSHIFT = auto()
    RSHIFT = auto()

    # Assignment operators
    ASSIGN = auto()
    PLUS_ASSIGN = auto()
    MINUS_ASSIGN = auto()
    STAR_ASSIGN = auto()
    SLASH_ASSIGN = auto()
    PERCENT_ASSIGN = auto()

    # Increment/Decrement
    INCREMENT = auto()
    DECREMENT = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACE = auto()
    RBRACE = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    SEMICOLON = auto()
    COMMA = auto()
    COLON = auto()

    # Special
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:{self.col})"


KEYWORDS = {
    "int": TokenType.INT, "char": TokenType.CHAR, "void": TokenType.VOID,
    "if": TokenType.IF, "else": TokenType.ELSE,
    "while": TokenType.WHILE, "for": TokenType.FOR, "do": TokenType.DO,
    "switch": TokenType.SWITCH, "case": TokenType.CASE, "default": TokenType.DEFAULT,
    "break": TokenType.BREAK, "continue": TokenType.CONTINUE, "return": TokenType.RETURN,
}
