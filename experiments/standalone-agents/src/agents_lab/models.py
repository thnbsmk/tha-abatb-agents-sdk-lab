"""Conversation types and the model abstraction that drives an agent loop.

A :class:`Model` inspects the conversation so far and decides the next action: either
call a tool (:class:`ToolCall`) or stop with a :class:`FinalAnswer`. :class:`MockModel`
is a deterministic, offline implementation so the lab runs end-to-end without any
external API keys.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from .agent import Agent


@dataclass
class Message:
    """A single conversation entry."""

    role: str  # "user" | "assistant" | "tool"
    content: str
    tool_name: str | None = None


@dataclass
class ToolCall:
    """A model's request to invoke a tool with keyword arguments."""

    tool: str
    arguments: dict[str, object]


@dataclass
class FinalAnswer:
    """A model's decision to stop and return ``content`` to the caller."""

    content: str


ModelAction = ToolCall | FinalAnswer


@runtime_checkable
class Model(Protocol):
    """Decides the next action given an agent and the conversation so far."""

    def decide(self, agent: Agent, conversation: list[Message]) -> ModelAction: ...


_EXPRESSION_RE = re.compile(r"[-+(]*\d[\d\s+\-*/().]*")


class MockModel:
    """A deterministic, dependency-free model for offline runs and tests.

    Policy: once a tool result is present, summarize it as the final answer. Otherwise,
    if the user's message contains an arithmetic expression and a ``calculator`` tool is
    available, call it; if an ``echo`` tool is available, echo the message; else answer
    directly.
    """

    def decide(self, agent: Agent, conversation: list[Message]) -> ModelAction:
        last = conversation[-1]

        if last.role == "tool":
            return FinalAnswer(content=f"The {last.tool_name} result is {last.content}.")

        available = {t.name for t in agent.tools}
        expression = self._extract_expression(last.content)
        if expression and "calculator" in available:
            return ToolCall(tool="calculator", arguments={"expression": expression})
        if "echo" in available:
            return ToolCall(tool="echo", arguments={"text": last.content})
        return FinalAnswer(content=f"{agent.name}: {last.content}")

    @staticmethod
    def _extract_expression(text: str) -> str | None:
        match = _EXPRESSION_RE.search(text)
        if match is None:
            return None
        candidate = match.group(0).strip()
        # Require a binary operator so bare numbers don't trigger the calculator.
        if any(op in candidate for op in "+*/") or "-" in candidate[1:]:
            return candidate
        return None
