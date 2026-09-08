"""End-to-end tests for the flexible offline rule-based model."""

from agents import Agent, Runner

from agents_lab.models import RuleBasedModel
from agents_lab.tools import add_tool, get_weather_tool, multiply_tool


def _agent() -> Agent:
    return Agent(
        name="Offline Test Agent",
        instructions="Use the provided tools.",
        model=RuleBasedModel(),
        tools=[add_tool, multiply_tool, get_weather_tool],
    )


def test_rule_based_addition():
    result = Runner.run_sync(_agent(), "what is 2 + 3?")
    assert "5" in result.final_output


def test_rule_based_multiplication():
    result = Runner.run_sync(_agent(), "please compute 21 times 2")
    assert "42" in result.final_output


def test_rule_based_weather():
    result = Runner.run_sync(_agent(), "what's the weather in Tokyo?")
    assert "clear" in result.final_output.lower()


def test_rule_based_help():
    result = Runner.run_sync(_agent(), "hello")
    assert "add or multiply" in result.final_output
