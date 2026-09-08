"""Tool definitions for the agents lab.

A :class:`Tool` wraps a plain Python callable together with the metadata an agent
needs to decide when to use it. The :func:`tool` decorator is the ergonomic way to
turn a function into a :class:`Tool`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, overload


@dataclass
class Tool:
    """A callable an agent can invoke, plus the metadata used to choose it."""

    name: str
    description: str
    func: Callable[..., Any]

    def invoke(self, arguments: dict[str, Any]) -> str:
        """Call the underlying function with keyword ``arguments`` and stringify the result."""
        return str(self.func(**arguments))


@overload
def tool(func: Callable[..., Any]) -> Tool: ...


@overload
def tool(
    *, name: str | None = ..., description: str | None = ...
) -> Callable[[Callable[..., Any]], Tool]: ...


def tool(
    func: Callable[..., Any] | None = None,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Tool | Callable[[Callable[..., Any]], Tool]:
    """Turn a function into a :class:`Tool`.

    Usable bare (``@tool``) or with keyword overrides (``@tool(name=...)``). The tool
    name defaults to the function name and the description to its docstring.
    """

    def wrap(f: Callable[..., Any]) -> Tool:
        return Tool(
            name=name or f.__name__,
            description=description or (f.__doc__ or "").strip(),
            func=f,
        )

    if func is not None:
        return wrap(func)
    return wrap
