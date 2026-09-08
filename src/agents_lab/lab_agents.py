"""Agent definitions for the lab.

The lab wires up a small multi-agent setup:

* a *triage* agent that can answer general questions, use tools, and hand off to
  a specialist;
* a *weather specialist* agent focused on weather questions.

Every builder accepts an optional ``model`` so tests and the offline demo can
inject a scripted :class:`~agents_lab.fake_model.FakeModel` instead of calling a
real LLM.
"""

from __future__ import annotations

from agents import Agent
from agents.models.interface import Model

from .tools import add_tool, get_weather_tool


def build_weather_specialist(model: Model | str | None = None) -> Agent:
    """Agent that specializes in weather questions."""
    return Agent(
        name="Weather Specialist",
        instructions=(
            "You are a meteorologist. Use the get_weather tool to answer weather "
            "questions and reply with one concise sentence."
        ),
        tools=[get_weather_tool],
        model=model,
    )


def build_triage_agent(model: Model | str | None = None) -> Agent:
    """Front-line agent that answers general questions or hands off to a specialist.

    The same ``model`` is shared with the specialist so an offline scripted model
    can drive the full handoff flow deterministically.
    """
    specialist = build_weather_specialist(model=model)
    return Agent(
        name="Triage Agent",
        instructions=(
            "You are a helpful assistant. Use the add tool for arithmetic. "
            "For anything about the weather, hand off to the Weather Specialist."
        ),
        tools=[add_tool],
        handoffs=[specialist],
        model=model,
    )
