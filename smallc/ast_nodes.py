"""AST node definitions for Small-C."""

from dataclasses import dataclass, field


@dataclass
class ASTNode:
    line: int = 0
    col: int = 0


# ── Program ──
@dataclass
class Program(ASTNode):
    declarations: list = field(default_factory=list)


# ── Declarations ──
@dataclass
class VarDeclaration(ASTNode):
    var_type: str = ""
    name: str = ""
    is_pointer: bool = False
    array_size: int | None = None
    initializer: ASTNode | None = None


@dataclass
class ParamDecl(ASTNode):
    param_type: str = ""
    name: str = ""
    is_pointer: bool = False
    is_array: bool = False


@dataclass
class FunctionDef(ASTNode):
    return_type: str = ""
    name: str = ""
    params: list = field(default_factory=list)
    body: ASTNode | None = None


# ── Statements ──
@dataclass
class Block(ASTNode):
    statements: list = field(default_factory=list)


@dataclass
class IfStatement(ASTNode):
    condition: ASTNode | None = None
    then_branch: ASTNode | None = None
    else_branch: ASTNode | None = None


@dataclass
class WhileLoop(ASTNode):
    condition: ASTNode | None = None
    body: ASTNode | None = None


@dataclass
class DoWhileLoop(ASTNode):
    body: ASTNode | None = None
    condition: ASTNode | None = None


@dataclass
class ForLoop(ASTNode):
    init: ASTNode | None = None
    condition: ASTNode | None = None
    update: ASTNode | None = None
    body: ASTNode | None = None


@dataclass
class SwitchStatement(ASTNode):
    expr: ASTNode | None = None
    cases: list = field(default_factory=list)
    default: ASTNode | None = None


@dataclass
class CaseClause(ASTNode):
    value: ASTNode | None = None
    body: list = field(default_factory=list)


@dataclass
class ReturnStatement(ASTNode):
    value: ASTNode | None = None


@dataclass
class BreakStatement(ASTNode):
    pass


@dataclass
class ContinueStatement(ASTNode):
    pass


@dataclass
class ExpressionStatement(ASTNode):
    expr: ASTNode | None = None


# ── Expressions ──
@dataclass
class BinaryOp(ASTNode):
    op: str = ""
    left: ASTNode | None = None
    right: ASTNode | None = None


@dataclass
class UnaryOp(ASTNode):
    op: str = ""
    operand: ASTNode | None = None


@dataclass
class PostfixOp(ASTNode):
    op: str = ""
    operand: ASTNode | None = None


@dataclass
class Assignment(ASTNode):
    target: ASTNode | None = None
    op: str = "="
    value: ASTNode | None = None


@dataclass
class FunctionCall(ASTNode):
    name: str = ""
    arguments: list = field(default_factory=list)


@dataclass
class ArrayAccess(ASTNode):
    array: ASTNode | None = None
    index: ASTNode | None = None


@dataclass
class Identifier(ASTNode):
    name: str = ""


@dataclass
class IntLiteral(ASTNode):
    value: int = 0


@dataclass
class CharLiteral(ASTNode):
    value: str = ""


@dataclass
class StringLiteral(ASTNode):
    value: str = ""


@dataclass
class CastExpr(ASTNode):
    target_type: str = ""
    expr: ASTNode | None = None


@dataclass
class ArrayInitList(ASTNode):
    elements: list = field(default_factory=list)
