"""End-to-end agent tests driven by the offline scripted FakeModel.

These prove the full runner loop works (tool calling + multi-agent handoff)
without any network access or API key.
"""

import json

from agents import Handoff, Runner

from agents_lab import (
    FakeModel,
    build_triage_agent,
    build_weather_specialist,
    text_message,
    tool_call,
)


def test_tool_calling_flow():
    model = FakeModel(
        [
            [tool_call("add", json.dumps({"a": 2, "b": 3}))],
            [text_message("The answer is 5.")],
        ]
    )
    agent = build_triage_agent(model=model)

    result = Runner.run_sync(agent, "What is 2 + 3?")

    assert result.final_output == "The answer is 5."
    # Two model calls: one to request the tool, one to produce the final answer.
    assert model.calls == 2
    assert result.last_agent.name == "Triage Agent"


def test_handoff_flow():
    handoff_name = Handoff.default_tool_name(build_weather_specialist())
    model = FakeModel(
        [
            [tool_call(handoff_name, "{}")],
            [tool_call("get_weather", json.dumps({"city": "Tokyo"}))],
            [text_message("Tokyo is 24C and clear.")],
        ]
    )
    agent = build_triage_agent(model=model)

    result = Runner.run_sync(agent, "What's the weather in Tokyo?")

    assert result.final_output == "Tokyo is 24C and clear."
    # Control was handed off to the specialist.
    assert result.last_agent.name == "Weather Specialist"
    assert model.calls == 3
