"""A ready-to-run demo agent with a couple of safe, dependency-free tools."""

from __future__ import annotations

import ast
import operator
from collections.abc import Callable

from .agent import Agent
from .tools import tool

_BIN_OPS: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type[ast.unaryop], Callable[[float], float]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        return _BIN_OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def safe_eval(expression: str) -> float:
    """Evaluate a basic arithmetic ``expression`` without using :func:`eval`."""
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree.body)


@tool(description="Evaluate a basic arithmetic expression, e.g. '(6 * 7) + 3'.")
def calculator(expression: str) -> float:
    """Compute the value of an arithmetic expression."""
    return safe_eval(expression)


@tool(description="Repeat the given text back to the caller.")
def echo(text: str) -> str:
    """Return ``text`` unchanged."""
    return text


def build_demo_agent() -> Agent:
    """Build the default demo agent used by the CLI and tests."""
    return Agent(
        name="lab-assistant",
        instructions="Help the user by using tools when appropriate.",
        tools=[calculator, echo],
    )
