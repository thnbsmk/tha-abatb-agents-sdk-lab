"""agents_lab: a small, offline-runnable lab for the OpenAI Agents SDK.

The package pairs real ``agents`` SDK primitives (``Agent``, ``Runner``,
function tools) with local model implementations so the examples and tests run
end to end without network access or an API key.
"""

from .models import RuleBasedModel, ScriptedModel, text, tool_call
from .tools import add, get_weather, multiply

__all__ = [
    "RuleBasedModel",
    "ScriptedModel",
    "text",
    "tool_call",
    "add",
    "multiply",
    "get_weather",
]
