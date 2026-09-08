from __future__ import annotations

import pytest

from agents_lab import Tool, tool
from agents_lab.demo import safe_eval


def test_tool_decorator_infers_name_and_description() -> None:
    @tool
    def greet(name: str) -> str:
        """Say hello."""
        return f"hi {name}"

    assert isinstance(greet, Tool)
    assert greet.name == "greet"
    assert greet.description == "Say hello."
    assert greet.invoke({"name": "sam"}) == "hi sam"


def test_tool_decorator_with_overrides() -> None:
    @tool(name="adder", description="Add two ints.")
    def add(a: int, b: int) -> int:
        return a + b

    assert add.name == "adder"
    assert add.description == "Add two ints."
    assert add.invoke({"a": 2, "b": 3}) == "5"


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 1", 2.0),
        ("(6 * 7) + 3", 45.0),
        ("2 ** 10", 1024.0),
        ("-5 + 2", -3.0),
        ("10 / 4", 2.5),
    ],
)
def test_safe_eval(expression: str, expected: float) -> None:
    assert safe_eval(expression) == expected


def test_safe_eval_rejects_non_arithmetic() -> None:
    with pytest.raises(ValueError):
        safe_eval("__import__('os').system('echo hi')")
