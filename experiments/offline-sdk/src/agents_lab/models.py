"""Local, offline model implementations for the Agents SDK.

These models implement the SDK's :class:`agents.models.interface.Model`
interface without any network calls, so agents can be exercised deterministically
in tests and demos. Two flavors are provided:

* :class:`ScriptedModel` replays a fixed list of responses, one per model turn.
  This is ideal for deterministic tests.
* :class:`RuleBasedModel` inspects the conversation and decides whether to call a
  tool or answer directly, giving the demo a bit of dynamic behavior offline.
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Any

from agents.items import ModelResponse, TResponseStreamEvent
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)


@dataclass
class _Text:
    text: str


@dataclass
class _ToolCall:
    name: str
    arguments: dict[str, Any]
    call_id: str = "call_1"


def text(value: str) -> _Text:
    """Script a plain assistant text response."""
    return _Text(value)


def tool_call(name: str, call_id: str = "call_1", **arguments: Any) -> _ToolCall:
    """Script a function tool call response."""
    return _ToolCall(name=name, arguments=arguments, call_id=call_id)


def _text_item(value: str, item_id: str = "msg_1") -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id=item_id,
        type="message",
        role="assistant",
        status="completed",
        content=[ResponseOutputText(text=value, type="output_text", annotations=[])],
    )


def _tool_call_item(call: _ToolCall, item_id: str = "fc_1") -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(
        id=item_id,
        call_id=call.call_id,
        type="function_call",
        name=call.name,
        arguments=json.dumps(call.arguments),
        status="completed",
    )


def _to_output_item(step: _Text | _ToolCall):
    if isinstance(step, _Text):
        return _text_item(step.text)
    return _tool_call_item(step)


def _empty_usage() -> Usage:
    return Usage(requests=1)


class _BaseLocalModel(Model):
    """Shared plumbing for offline models."""

    def stream_response(  # type: ignore[override]
        self,
        *args: Any,
        **kwargs: Any,
    ) -> AsyncIterator[TResponseStreamEvent]:
        raise NotImplementedError(
            "Local lab models are non-streaming; use Runner.run (not run_streamed)."
        )


@dataclass
class ScriptedModel(_BaseLocalModel):
    """Return a predetermined response on each model turn.

    Each call to :meth:`get_response` pops the next scripted step. Use
    :func:`text` and :func:`tool_call` to build the script.
    """

    script: list[_Text | _ToolCall] = field(default_factory=list)
    _turn: int = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        if self._turn >= len(self.script):
            raise AssertionError(
                f"ScriptedModel ran out of scripted turns (asked for turn {self._turn})."
            )
        step = self.script[self._turn]
        self._turn += 1
        return ModelResponse(
            output=[_to_output_item(step)],
            usage=_empty_usage(),
            response_id=None,
        )


def _iter_items(input: str | Sequence[Any]) -> list[dict[str, Any]]:
    if isinstance(input, str):
        return [{"role": "user", "content": input}]
    items: list[dict[str, Any]] = []
    for it in input:
        if isinstance(it, dict):
            items.append(it)
        elif hasattr(it, "model_dump"):
            items.append(it.model_dump())
    return items


def _latest_user_text(items: list[dict[str, Any]]) -> str:
    for it in reversed(items):
        if it.get("role") == "user":
            content = it.get("content")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                parts = [p.get("text", "") for p in content if isinstance(p, dict)]
                return " ".join(parts)
    return ""


def _tool_outputs(items: list[dict[str, Any]]) -> list[str]:
    outputs: list[str] = []
    for it in items:
        if it.get("type") == "function_call_output":
            out = it.get("output")
            if isinstance(out, str):
                outputs.append(out)
            elif isinstance(out, dict):
                outputs.append(str(out.get("text") or out))
    return outputs


_ADD_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:\+|plus|and)\s*(-?\d+(?:\.\d+)?)")
_MUL_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:\*|x|times|multiplied by)\s*(-?\d+(?:\.\d+)?)")
_WEATHER_RE = re.compile(r"weather.*?\bin\b\s+([a-zA-Z .]+)", re.IGNORECASE)


class RuleBasedModel(_BaseLocalModel):
    """A tiny offline "planner" that decides tool calls from the prompt.

    It supports arithmetic (``add``/``multiply``) and weather lookups. When a
    tool has already produced output, it composes a final natural-language
    answer from that output.
    """

    async def get_response(  # type: ignore[override]
        self,
        system_instructions: str | None = None,
        input: str | Sequence[Any] = "",
        *args: Any,
        **kwargs: Any,
    ) -> ModelResponse:
        items = _iter_items(input)
        outputs = _tool_outputs(items)
        if outputs:
            answer = f"The result is {outputs[-1]}."
            step: _Text | _ToolCall = _Text(answer)
        else:
            step = self._plan(_latest_user_text(items))
        return ModelResponse(
            output=[_to_output_item(step)],
            usage=_empty_usage(),
            response_id=None,
        )

    @staticmethod
    def _plan(prompt: str) -> _Text | _ToolCall:
        if m := _MUL_RE.search(prompt):
            return _ToolCall("multiply", arguments={"a": float(m[1]), "b": float(m[2])})
        if m := _ADD_RE.search(prompt):
            return _ToolCall("add", arguments={"a": float(m[1]), "b": float(m[2])})
        if m := _WEATHER_RE.search(prompt):
            return _ToolCall("get_weather", arguments={"city": m[1].strip(" .")})
        return _Text(
            "I can add or multiply two numbers, or look up the weather in a city. "
            "Try: 'what is 2 + 3?' or 'weather in Tokyo'."
        )
