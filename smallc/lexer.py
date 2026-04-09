"""Lexical analyzer for Small-C."""

from .errors import LexerError
from .tokens import KEYWORDS, Token, TokenType


class Lexer:
    """Tokenizes Small-C source code."""

    def __init__(self, source: str, line_offset: int = 0):
        self.source = source
        self.pos = 0
        self.line = 1 + line_offset
        self.col = 1
        self.tokens: list[Token] = []

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            ch = self.source[self.pos]
            if ch.isdigit() or (ch == '0' and self._peek(1) in ('x', 'X')):
                self._read_number()
            elif ch.isalpha() or ch == '_':
                self._read_identifier()
            elif ch == '"':
                self._read_string()
            elif ch == "'":
                self._read_char_literal()
            else:
                self._read_operator_or_delimiter()
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.col))
        return self.tokens

    def _peek(self, offset: int = 0) -> str:
        p = self.pos + offset
        return self.source[p] if p < len(self.source) else '\0'

    def _advance(self) -> str:
        ch = self.source[self.pos]
        self.pos += 1
        if ch == '\n':
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in (' ', '\t', '\r', '\n'):
                self._advance()
            elif ch == '/' and self._peek(1) == '/':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self._advance()
            elif ch == '/' and self._peek(1) == '*':
                sl, sc = self.line, self.col
                self._advance(); self._advance()
                while self.pos < len(self.source):
                    if self.source[self.pos] == '*' and self._peek(1) == '/':
                        self._advance(); self._advance()
                        break
                    self._advance()
                else:
                    raise LexerError("unterminated block comment", sl, sc)
            else:
                break

    def _read_number(self):
        sl, sc = self.line, self.col
        s = ""
        if self.source[self.pos] == '0' and self._peek(1) in ('x', 'X'):
            s += self._advance(); s += self._advance()
            if self.pos >= len(self.source) or self.source[self.pos] not in "0123456789abcdefABCDEF":
                raise LexerError("invalid hex literal", sl, sc)
            while self.pos < len(self.source) and self.source[self.pos] in "0123456789abcdefABCDEF":
                s += self._advance()
        else:
            while self.pos < len(self.source) and self.source[self.pos].isdigit():
                s += self._advance()
        self.tokens.append(Token(TokenType.INT_LITERAL, s, sl, sc))

    def _read_identifier(self):
        sl, sc = self.line, self.col
        s = ""
        while self.pos < len(self.source) and (self.source[self.pos].isalnum() or self.source[self.pos] == '_'):
            s += self._advance()
        self.tokens.append(Token(KEYWORDS.get(s, TokenType.IDENTIFIER), s, sl, sc))

    def _read_string(self):
        sl, sc = self.line, self.col
        self._advance()
        v = ""
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\n':
                raise LexerError("unterminated string literal", sl, sc)
            if self.source[self.pos] == '\\':
                v += self._read_escape()
            else:
                v += self._advance()
        if self.pos >= len(self.source):
            raise LexerError("unterminated string literal", sl, sc)
        self._advance()
        self.tokens.append(Token(TokenType.STRING_LITERAL, v, sl, sc))

    def _read_char_literal(self):
        sl, sc = self.line, self.col
        self._advance()
        if self.pos >= len(self.source):
            raise LexerError("unterminated char literal", sl, sc)
        if self.source[self.pos] == '\\':
            v = self._read_escape()
        else:
            v = self._advance()
        if self.pos >= len(self.source) or self.source[self.pos] != "'":
            raise LexerError("unterminated char literal", sl, sc)
        self._advance()
        self.tokens.append(Token(TokenType.CHAR_LITERAL, v, sl, sc))

    def _read_escape(self) -> str:
        self._advance()
        if self.pos >= len(self.source):
            raise LexerError("unexpected end of escape sequence", self.line, self.col)
        ch = self._advance()
        m = {'n': '\n', 't': '\t', '0': '\0', '\\': '\\', "'": "'", '"': '"',
             'r': '\r', 'a': '\a', 'b': '\b'}
        if ch in m:
            return m[ch]
        raise LexerError(f"unknown escape sequence: \\{ch}", self.line, self.col - 1)

    def _read_operator_or_delimiter(self):
        sl, sc = self.line, self.col
        ch = self.source[self.pos]
        nch = self._peek(1)
        two = ch + nch if nch != '\0' else ""

        TWO_MAP = {
            '==': TokenType.EQ, '!=': TokenType.NEQ,
            '<=': TokenType.LTE, '>=': TokenType.GTE,
            '&&': TokenType.AND, '||': TokenType.OR,
            '<<': TokenType.LSHIFT, '>>': TokenType.RSHIFT,
            '++': TokenType.INCREMENT, '--': TokenType.DECREMENT,
            '+=': TokenType.PLUS_ASSIGN, '-=': TokenType.MINUS_ASSIGN,
            '*=': TokenType.STAR_ASSIGN, '/=': TokenType.SLASH_ASSIGN,
            '%=': TokenType.PERCENT_ASSIGN,
        }
        if two in TWO_MAP:
            self._advance(); self._advance()
            self.tokens.append(Token(TWO_MAP[two], two, sl, sc))
            return

        ONE_MAP = {
            '+': TokenType.PLUS, '-': TokenType.MINUS,
            '*': TokenType.STAR, '/': TokenType.SLASH,
            '%': TokenType.PERCENT, '&': TokenType.AMP,
            '|': TokenType.PIPE, '^': TokenType.CARET,
            '~': TokenType.TILDE, '!': TokenType.NOT,
            '<': TokenType.LT, '>': TokenType.GT,
            '=': TokenType.ASSIGN,
            '(': TokenType.LPAREN, ')': TokenType.RPAREN,
            '{': TokenType.LBRACE, '}': TokenType.RBRACE,
            '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
            ';': TokenType.SEMICOLON, ',': TokenType.COMMA,
            ':': TokenType.COLON,
        }
        if ch in ONE_MAP:
            self._advance()
            self.tokens.append(Token(ONE_MAP[ch], ch, sl, sc))
            return
        raise LexerError(f"unexpected character: {ch!r}", sl, sc)
