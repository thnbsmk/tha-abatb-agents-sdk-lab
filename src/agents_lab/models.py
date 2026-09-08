"""Rule-based offline model for interactive Agents SDK experiments."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator, Sequence
from typing import Any

from agents import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

_ADD_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*(?:\+|plus|and)\s*(-?\d+(?:\.\d+)?)")
_MUL_RE = re.compile(
    r"(-?\d+(?:\.\d+)?)\s*(?:\*|x|times|multiplied by)\s*(-?\d+(?:\.\d+)?)"
)
_WEATHER_RE = re.compile(r"weather.*?\bin\b\s+([a-zA-Z .]+)", re.IGNORECASE)


def _message(text: str) -> ResponseOutputMessage:
    return ResponseOutputMessage(
        id="msg_rule_based",
        role="assistant",
        status="completed",
        type="message",
        content=[ResponseOutputText(text=text, type="output_text", annotations=[])],
    )


def _tool_call(name: str, **arguments: Any) -> ResponseFunctionToolCall:
    return ResponseFunctionToolCall(
        id="fc_rule_based",
        call_id="call_rule_based",
        name=name,
        arguments=json.dumps(arguments),
        type="function_call",
    )


def _items(model_input: str | Sequence[Any]) -> list[dict[str, Any]]:
    if isinstance(model_input, str):
        return [{"role": "user", "content": model_input}]
    items: list[dict[str, Any]] = []
    for item in model_input:
        if isinstance(item, dict):
            items.append(item)
        elif hasattr(item, "model_dump"):
            items.append(item.model_dump())
    return items


def _latest_user_text(items: list[dict[str, Any]]) -> str:
    for item in reversed(items):
        if item.get("role") != "user":
            continue
        content = item.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return " ".join(
                part.get("text", "") for part in content if isinstance(part, dict)
            )
    return ""


def _latest_tool_output(items: list[dict[str, Any]]) -> str | None:
    for item in reversed(items):
        if item.get("type") == "function_call_output":
            output = item.get("output")
            return output if isinstance(output, str) else str(output)
    return None


class RuleBasedModel(Model):
    """Choose the lab's arithmetic and weather tools without network access."""

    async def get_response(
        self,
        system_instructions: str | None = None,
        input: str | Sequence[Any] = "",
        *args: Any,
        **kwargs: Any,
    ) -> ModelResponse:
        items = _items(input)
        tool_output = _latest_tool_output(items)
        if tool_output is not None:
            output = [_message(f"The result is {tool_output}.")]
        else:
            output = [self._plan(_latest_user_text(items))]
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    @staticmethod
    def _plan(prompt: str) -> ResponseFunctionToolCall | ResponseOutputMessage:
        if match := _MUL_RE.search(prompt):
            return _tool_call("multiply", a=float(match[1]), b=float(match[2]))
        if match := _ADD_RE.search(prompt):
            return _tool_call("add", a=float(match[1]), b=float(match[2]))
        if match := _WEATHER_RE.search(prompt):
            return _tool_call("get_weather", city=match[1].strip(" .?"))
        return _message(
            "I can add or multiply two numbers, or look up weather. "
            "Try 'what is 2 + 3?' or 'weather in Tokyo'."
        )

    def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        raise NotImplementedError("RuleBasedModel does not support streaming")
