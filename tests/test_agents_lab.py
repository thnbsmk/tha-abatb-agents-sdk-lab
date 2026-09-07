"""End-to-end tests that run real Agents SDK agents against offline models."""

from __future__ import annotations

import pytest
from agents import Agent, Runner

from agents_lab.demo import build_agent, run_prompt
from agents_lab.models import RuleBasedModel, ScriptedModel, text, tool_call
from agents_lab.tools import add, get_weather, multiply


@pytest.mark.asyncio
async def test_scripted_model_runs_tool_then_answers():
    model = ScriptedModel(
        script=[
            tool_call("add", a=2, b=3),
            text("The sum is 5."),
        ]
    )
    agent = Agent(name="T", instructions="Add numbers.", model=model, tools=[add])
    result = await Runner.run(agent, "add 2 and 3")
    assert result.final_output == "The sum is 5."


@pytest.mark.asyncio
async def test_rule_based_addition():
    agent = Agent(name="R", instructions="", model=RuleBasedModel(), tools=[add, multiply])
    result = await Runner.run(agent, "what is 2 + 3?")
    assert "5" in result.final_output


@pytest.mark.asyncio
async def test_rule_based_multiplication():
    agent = Agent(name="R", instructions="", model=RuleBasedModel(), tools=[add, multiply])
    result = await Runner.run(agent, "please compute 21 times 2")
    assert "42" in result.final_output


@pytest.mark.asyncio
async def test_rule_based_weather():
    agent = Agent(name="R", instructions="", model=RuleBasedModel(), tools=[get_weather])
    result = await Runner.run(agent, "what's the weather in Tokyo?")
    assert "clear" in result.final_output.lower()


def test_demo_build_and_run_sync():
    agent = build_agent()
    assert run_prompt(agent, "what is 10 + 5?").strip()
    assert "15" in run_prompt(agent, "what is 10 + 5?")
