"""Recursive-descent parser for Small-C."""

from .ast_nodes import *
from .errors import ParseError
from .tokens import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        prog = Program(line=1, col=1)
        while not self._at_end():
            d = self._parse_top_level()
            if d:
                prog.declarations.append(d)
        return prog

    # ── helpers ──

    def _cur(self) -> Token:
        return self.tokens[self.pos]

    def _at_end(self) -> bool:
        return self._cur().type == TokenType.EOF

    def _peek(self, off: int = 0) -> Token:
        i = self.pos + off
        return self.tokens[i] if i < len(self.tokens) else self.tokens[-1]

    def _advance(self) -> Token:
        t = self._cur()
        if not self._at_end():
            self.pos += 1
        return t

    def _check(self, *tt: TokenType) -> bool:
        return self._cur().type in tt

    def _match(self, *tt: TokenType) -> Token | None:
        if self._cur().type in tt:
            return self._advance()
        return None

    def _expect(self, tt: TokenType, msg: str = "") -> Token:
        if self._cur().type == tt:
            return self._advance()
        t = self._cur()
        m = msg or f"expected '{_tok_name(tt)}', got '{t.value}'"
        raise ParseError(m, t.line, t.col)

    def _is_type(self) -> bool:
        return self._cur().type in (TokenType.INT, TokenType.CHAR, TokenType.VOID)

    # ── top level ──

    def _parse_top_level(self):
        if self._at_end():
            return None
        if not self._is_type():
            # treat as statement in global context
            return self._parse_statement()
        # look ahead: type [*] name ( → function, else → var decl
        saved = self.pos
        self._advance()  # type
        if self._match(TokenType.STAR):
            pass
        if not self._check(TokenType.IDENTIFIER):
            self.pos = saved
            return self._parse_statement()
        self._advance()  # name
        is_func = self._check(TokenType.LPAREN)
        self.pos = saved

        if is_func:
            return self._parse_function_def()
        return self._parse_var_declaration()

    def _parse_function_def(self) -> FunctionDef:
        type_tok = self._advance()
        ret_type = type_tok.value
        is_ptr = bool(self._match(TokenType.STAR))
        if is_ptr:
            ret_type += '*'
        name_tok = self._expect(TokenType.IDENTIFIER)
        self._expect(TokenType.LPAREN)
        params = self._parse_params()
        self._expect(TokenType.RPAREN)
        body = self._parse_block()
        return FunctionDef(return_type=ret_type, name=name_tok.value,
                           params=params, body=body,
                           line=type_tok.line, col=type_tok.col)

    def _parse_params(self) -> list[ParamDecl]:
        params = []
        if self._check(TokenType.RPAREN):
            return params
        if self._check(TokenType.VOID) and self._peek(1).type == TokenType.RPAREN:
            self._advance()
            return params
        params.append(self._parse_one_param())
        while self._match(TokenType.COMMA):
            params.append(self._parse_one_param())
        return params

    def _parse_one_param(self) -> ParamDecl:
        if not self._is_type():
            raise ParseError("expected type in parameter", self._cur().line, self._cur().col)
        tt = self._advance()
        is_ptr = bool(self._match(TokenType.STAR))
        nm = self._expect(TokenType.IDENTIFIER)
        is_arr = False
        if self._match(TokenType.LBRACKET):
            self._expect(TokenType.RBRACKET)
            is_arr = True
        return ParamDecl(param_type=tt.value, name=nm.value,
                         is_pointer=is_ptr, is_array=is_arr,
                         line=tt.line, col=tt.col)

    # ── declarations ──

    def _parse_var_declaration(self) -> VarDeclaration:
        tt = self._advance()
        is_ptr = bool(self._match(TokenType.STAR))
        nm = self._expect(TokenType.IDENTIFIER)
        arr_sz = None
        if self._match(TokenType.LBRACKET):
            sz = self._expect(TokenType.INT_LITERAL, "expected array size")
            arr_sz = int(sz.value)
            self._expect(TokenType.RBRACKET)
        init = None
        if self._match(TokenType.ASSIGN):
            if arr_sz is not None and self._check(TokenType.LBRACE):
                init = self._parse_array_init()
            else:
                init = self._parse_assignment_expr()
        self._expect(TokenType.SEMICOLON, "expected ';' after declaration")
        return VarDeclaration(var_type=tt.value, name=nm.value,
                              is_pointer=is_ptr, array_size=arr_sz,
                              initializer=init, line=tt.line, col=tt.col)

    def _parse_array_init(self) -> ArrayInitList:
        self._expect(TokenType.LBRACE)
        elems = []
        if not self._check(TokenType.RBRACE):
            elems.append(self._parse_assignment_expr())
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RBRACE):
                    break
                elems.append(self._parse_assignment_expr())
        self._expect(TokenType.RBRACE)
        return ArrayInitList(elements=elems,
                             line=elems[0].line if elems else 0, col=0)

    # ── statements ──

    def _parse_statement(self):
        t = self._cur()
        if t.type == TokenType.LBRACE:
            return self._parse_block()
        if t.type == TokenType.IF:
            return self._parse_if()
        if t.type == TokenType.WHILE:
            return self._parse_while()
        if t.type == TokenType.DO:
            return self._parse_do_while()
        if t.type == TokenType.FOR:
            return self._parse_for()
        if t.type == TokenType.SWITCH:
            return self._parse_switch()
        if t.type == TokenType.RETURN:
            return self._parse_return()
        if t.type == TokenType.BREAK:
            self._advance()
            self._expect(TokenType.SEMICOLON)
            return BreakStatement(line=t.line, col=t.col)
        if t.type == TokenType.CONTINUE:
            self._advance()
            self._expect(TokenType.SEMICOLON)
            return ContinueStatement(line=t.line, col=t.col)
        if self._is_type() and self._cur().type != TokenType.VOID:
            return self._parse_var_declaration()
        expr = self._parse_expression()
        self._expect(TokenType.SEMICOLON, "expected ';' after expression statement")
        return ExpressionStatement(expr=expr, line=t.line, col=t.col)

    def _parse_block(self) -> Block:
        t = self._expect(TokenType.LBRACE)
        stmts = []
        while not self._check(TokenType.RBRACE) and not self._at_end():
            stmts.append(self._parse_statement())
        self._expect(TokenType.RBRACE, "expected '}'")
        return Block(statements=stmts, line=t.line, col=t.col)

    def _parse_if(self) -> IfStatement:
        t = self._advance()
        self._expect(TokenType.LPAREN)
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN, "expected ')' after condition")
        then_b = self._parse_statement()
        else_b = None
        if self._match(TokenType.ELSE):
            else_b = self._parse_statement()
        return IfStatement(condition=cond, then_branch=then_b,
                           else_branch=else_b, line=t.line, col=t.col)

    def _parse_while(self) -> WhileLoop:
        t = self._advance()
        self._expect(TokenType.LPAREN)
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN)
        body = self._parse_statement()
        return WhileLoop(condition=cond, body=body, line=t.line, col=t.col)

    def _parse_do_while(self) -> DoWhileLoop:
        t = self._advance()  # do
        body = self._parse_statement()
        self._expect(TokenType.WHILE, "expected 'while' after do-block")
        self._expect(TokenType.LPAREN)
        cond = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.SEMICOLON, "expected ';' after do-while")
        return DoWhileLoop(body=body, condition=cond, line=t.line, col=t.col)

    def _parse_for(self) -> ForLoop:
        t = self._advance()
        self._expect(TokenType.LPAREN)
        init = None
        if not self._check(TokenType.SEMICOLON):
            if self._is_type() and self._cur().type != TokenType.VOID:
                init = self._parse_var_declaration()
            else:
                init = ExpressionStatement(expr=self._parse_expression(),
                                           line=self._cur().line, col=self._cur().col)
                self._expect(TokenType.SEMICOLON)
        else:
            self._advance()
        cond = None
        if not self._check(TokenType.SEMICOLON):
            cond = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        update = None
        if not self._check(TokenType.RPAREN):
            update = self._parse_expression()
        self._expect(TokenType.RPAREN)
        body = self._parse_statement()
        return ForLoop(init=init, condition=cond, update=update,
                       body=body, line=t.line, col=t.col)

    def _parse_switch(self) -> SwitchStatement:
        t = self._advance()
        self._expect(TokenType.LPAREN)
        expr = self._parse_expression()
        self._expect(TokenType.RPAREN)
        self._expect(TokenType.LBRACE)
        cases = []
        default = None
        while not self._check(TokenType.RBRACE) and not self._at_end():
            if self._match(TokenType.CASE):
                cv = self._parse_expression()
                self._expect(TokenType.COLON)
                body = []
                while not self._check(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE):
                    body.append(self._parse_statement())
                cases.append(CaseClause(value=cv, body=body, line=cv.line, col=cv.col))
            elif self._match(TokenType.DEFAULT):
                self._expect(TokenType.COLON)
                stmts = []
                while not self._check(TokenType.CASE, TokenType.RBRACE):
                    stmts.append(self._parse_statement())
                default = Block(statements=stmts, line=t.line, col=t.col)
            else:
                raise ParseError("expected 'case' or 'default'",
                                 self._cur().line, self._cur().col)
        self._expect(TokenType.RBRACE)
        return SwitchStatement(expr=expr, cases=cases, default=default,
                               line=t.line, col=t.col)

    def _parse_return(self) -> ReturnStatement:
        t = self._advance()
        v = None
        if not self._check(TokenType.SEMICOLON):
            v = self._parse_expression()
        self._expect(TokenType.SEMICOLON)
        return ReturnStatement(value=v, line=t.line, col=t.col)

    # ── expressions (precedence climbing) ──

    def _parse_expression(self):
        return self._parse_assignment_expr()

    def _parse_assignment_expr(self):
        left = self._parse_logical_or()
        aops = {TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN, TokenType.PERCENT_ASSIGN}
        if self._cur().type in aops:
            op = self._advance()
            right = self._parse_assignment_expr()
            return Assignment(target=left, op=op.value, value=right,
                              line=op.line, col=op.col)
        return left

    def _parse_logical_or(self):
        left = self._parse_logical_and()
        while self._check(TokenType.OR):
            op = self._advance()
            right = self._parse_logical_and()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_logical_and(self):
        left = self._parse_bitwise_or()
        while self._check(TokenType.AND):
            op = self._advance()
            right = self._parse_bitwise_or()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_bitwise_or(self):
        left = self._parse_bitwise_xor()
        while self._check(TokenType.PIPE):
            op = self._advance()
            right = self._parse_bitwise_xor()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_bitwise_xor(self):
        left = self._parse_bitwise_and()
        while self._check(TokenType.CARET):
            op = self._advance()
            right = self._parse_bitwise_and()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_bitwise_and(self):
        left = self._parse_equality()
        while self._check(TokenType.AMP):
            op = self._advance()
            right = self._parse_equality()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_equality(self):
        left = self._parse_relational()
        while self._check(TokenType.EQ, TokenType.NEQ):
            op = self._advance()
            right = self._parse_relational()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_relational(self):
        left = self._parse_shift()
        while self._check(TokenType.LT, TokenType.GT, TokenType.LTE, TokenType.GTE):
            op = self._advance()
            right = self._parse_shift()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_shift(self):
        left = self._parse_additive()
        while self._check(TokenType.LSHIFT, TokenType.RSHIFT):
            op = self._advance()
            right = self._parse_additive()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_additive(self):
        left = self._parse_multiplicative()
        while self._check(TokenType.PLUS, TokenType.MINUS):
            op = self._advance()
            right = self._parse_multiplicative()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_multiplicative(self):
        left = self._parse_unary()
        while self._check(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._advance()
            right = self._parse_unary()
            left = BinaryOp(op=op.value, left=left, right=right, line=op.line, col=op.col)
        return left

    def _parse_unary(self):
        t = self._cur()
        # cast
        if t.type == TokenType.LPAREN and self._peek(1).type in (TokenType.INT, TokenType.CHAR):
            if self._peek(2).type == TokenType.RPAREN:
                self._advance(); tt = self._advance(); self._advance()
                e = self._parse_unary()
                return CastExpr(target_type=tt.value, expr=e, line=t.line, col=t.col)
        if self._check(TokenType.MINUS, TokenType.NOT, TokenType.TILDE):
            op = self._advance()
            return UnaryOp(op=op.value, operand=self._parse_unary(), line=op.line, col=op.col)
        if self._check(TokenType.AMP):
            op = self._advance()
            return UnaryOp(op='&', operand=self._parse_unary(), line=op.line, col=op.col)
        if self._check(TokenType.STAR):
            op = self._advance()
            return UnaryOp(op='*', operand=self._parse_unary(), line=op.line, col=op.col)
        if self._check(TokenType.INCREMENT, TokenType.DECREMENT):
            op = self._advance()
            return UnaryOp(op=op.value, operand=self._parse_unary(), line=op.line, col=op.col)
        return self._parse_postfix()

    def _parse_postfix(self):
        left = self._parse_primary()
        while True:
            if self._check(TokenType.LBRACKET):
                self._advance()
                idx = self._parse_expression()
                self._expect(TokenType.RBRACKET)
                left = ArrayAccess(array=left, index=idx, line=left.line, col=left.col)
            elif self._check(TokenType.LPAREN) and isinstance(left, Identifier):
                self._advance()
                args = []
                if not self._check(TokenType.RPAREN):
                    args.append(self._parse_assignment_expr())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_assignment_expr())
                self._expect(TokenType.RPAREN)
                left = FunctionCall(name=left.name, arguments=args,
                                    line=left.line, col=left.col)
            elif self._check(TokenType.INCREMENT, TokenType.DECREMENT):
                op = self._advance()
                left = PostfixOp(op=op.value, operand=left, line=op.line, col=op.col)
            else:
                break
        return left

    def _parse_primary(self):
        t = self._cur()
        if t.type == TokenType.INT_LITERAL:
            self._advance()
            v = int(t.value, 16) if t.value.startswith(('0x', '0X')) else int(t.value)
            return IntLiteral(value=v, line=t.line, col=t.col)
        if t.type == TokenType.CHAR_LITERAL:
            self._advance()
            return CharLiteral(value=t.value, line=t.line, col=t.col)
        if t.type == TokenType.STRING_LITERAL:
            self._advance()
            return StringLiteral(value=t.value, line=t.line, col=t.col)
        if t.type == TokenType.IDENTIFIER:
            self._advance()
            return Identifier(name=t.value, line=t.line, col=t.col)
        if t.type == TokenType.LPAREN:
            self._advance()
            e = self._parse_expression()
            self._expect(TokenType.RPAREN, "expected ')'")
            return e
        raise ParseError(f"unexpected token '{t.value}', expected expression",
                         t.line, t.col)


def _tok_name(tt: TokenType) -> str:
    m = {TokenType.SEMICOLON: ';', TokenType.RPAREN: ')', TokenType.RBRACE: '}',
         TokenType.RBRACKET: ']', TokenType.LPAREN: '(', TokenType.LBRACE: '{'}
    return m.get(tt, tt.name.lower())
