"""agents_lab: a hands-on lab for the OpenAI Agents SDK."""

from .fake_model import FakeModel, text_message, tool_call
from .lab_agents import build_triage_agent, build_weather_specialist
from .tools import add, add_tool, get_weather, get_weather_tool

__all__ = [
    "FakeModel",
    "text_message",
    "tool_call",
    "build_triage_agent",
    "build_weather_specialist",
    "add",
    "add_tool",
    "get_weather",
    "get_weather_tool",
]
