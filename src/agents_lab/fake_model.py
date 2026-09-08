"""A scripted, offline :class:`~agents.models.interface.Model` implementation.

The real Agents SDK talks to an LLM over the network. For deterministic tests
and for demoing the environment without an API key, ``FakeModel`` returns a
pre-scripted sequence of "turns". Each turn is a list of output items (a text
message and/or one or more tool/handoff calls) that the SDK's runner interprets
exactly as if they came from a real model.
"""

from __future__ import annotations

import itertools
from collections.abc import AsyncIterator
from typing import Any

from agents import ModelResponse
from agents.models.interface import Model
from agents.usage import Usage
from openai.types.responses import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
    ResponseOutputText,
)

_call_counter = itertools.count(1)


def text_message(text: str) -> ResponseOutputMessage:
    """Build a final assistant text message output item."""
    return ResponseOutputMessage(
        id="msg_fake",
        role="assistant",
        status="completed",
        type="message",
        content=[
            ResponseOutputText(text=text, type="output_text", annotations=[]),
        ],
    )


def tool_call(name: str, arguments: str, call_id: str | None = None) -> ResponseFunctionToolCall:
    """Build a function/handoff tool-call output item.

    ``name`` is the tool name (for a handoff this is ``transfer_to_<agent>``) and
    ``arguments`` is a JSON string of the call arguments. A unique ``call_id`` is
    generated automatically because the SDK rejects reused tool-call IDs.
    """
    n = next(_call_counter)
    resolved_call_id = call_id or f"call_fake_{n}"
    return ResponseFunctionToolCall(
        id=f"fc_fake_{n}",
        call_id=resolved_call_id,
        name=name,
        arguments=arguments,
        type="function_call",
    )


class FakeModel(Model):
    """Return scripted turns instead of calling a real model.

    Parameters
    ----------
    turns:
        A list of turns. Each turn is a list of output items produced by the
        helpers above. The runner requests one turn per model call, so a
        tool-calling turn should be followed by a turn containing the final text.
    """

    def __init__(self, turns: list[list[Any]]):
        self._turns = list(turns)
        self.calls = 0

    async def get_response(self, *args: Any, **kwargs: Any) -> ModelResponse:
        self.calls += 1
        if not self._turns:
            raise AssertionError("FakeModel ran out of scripted turns")
        output = self._turns.pop(0)
        return ModelResponse(output=output, usage=Usage(), response_id=None)

    def stream_response(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        raise NotImplementedError("FakeModel does not support streaming responses")
