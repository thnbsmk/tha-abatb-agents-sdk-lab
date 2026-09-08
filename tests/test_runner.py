from __future__ import annotations

from agents_lab import Agent, FinalAnswer, Message, Runner, ToolCall, build_demo_agent
from agents_lab.models import Model, ModelAction


def test_calculator_flow_uses_tool_then_answers() -> None:
    agent = build_demo_agent()
    result = Runner.run(agent, "Compute (6 * 7) + 3")

    assert result.final_output == "The calculator result is 45.0."
    tool_calls = [s for s in result.steps if isinstance(s.action, ToolCall)]
    assert len(tool_calls) == 1
    assert tool_calls[0].action.tool == "calculator"
    assert tool_calls[0].observation == "45.0"


def test_echo_flow_when_no_expression() -> None:
    agent = build_demo_agent()
    result = Runner.run(agent, "hello there")

    assert result.final_output == "The echo result is hello there."


def test_unknown_tool_is_reported_not_crashed() -> None:
    class AlwaysCallsMissingTool:
        def __init__(self) -> None:
            self._called = False

        def decide(self, agent: Agent, conversation: list[Message]) -> ModelAction:
            if not self._called:
                self._called = True
                return ToolCall(tool="does_not_exist", arguments={})
            return FinalAnswer(content="done")

    model: Model = AlwaysCallsMissingTool()
    agent = Agent(name="t", model=model)
    result = Runner.run(agent, "go")

    assert result.final_output == "done"
    assert result.steps[0].observation == "Error: unknown tool 'does_not_exist'"


def test_max_steps_guard() -> None:
    class NeverFinishes:
        def decide(self, agent: Agent, conversation: list[Message]) -> ModelAction:
            return ToolCall(tool="echo", arguments={"text": "loop"})

    agent = build_demo_agent()
    agent.model = NeverFinishes()
    try:
        Runner.run(agent, "spin", max_steps=3)
    except RuntimeError as exc:
        assert "max_steps=3" in str(exc)
    else:  # pragma: no cover - the guard must raise
        raise AssertionError("Runner did not enforce max_steps")
