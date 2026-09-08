"""Command-line demos for the OpenAI Agents SDK lab."""

from __future__ import annotations

import argparse
import json
import os
import sys

from agents import Agent, Handoff, Runner, set_tracing_disabled

from .fake_model import FakeModel, text_message, tool_call
from .lab_agents import build_triage_agent, build_weather_specialist
from .models import RuleBasedModel
from .tools import add_tool, get_weather_tool, multiply_tool

EXAMPLE_PROMPTS = [
    "What is 2 + 3?",
    "Please multiply 21 times 2.",
    "What's the weather in Tokyo?",
]


def _offline_model() -> FakeModel:
    """Script two independent runs for the offline demo.

    Run 1 (arithmetic): triage agent calls ``add`` then answers.
    Run 2 (weather): triage agent hands off to the specialist, which calls
    ``get_weather`` then answers.
    """
    handoff_name = Handoff.default_tool_name(build_weather_specialist())
    return FakeModel(
        [
            # --- Run 1: arithmetic via the add tool ---
            [tool_call("add", json.dumps({"a": 2, "b": 3}))],
            [text_message("2 + 3 = 5.")],
            # --- Run 2: handoff to the weather specialist ---
            [tool_call(handoff_name, "{}")],
            [tool_call("get_weather", json.dumps({"city": "Tokyo"}))],
            [text_message("The weather in Tokyo is 24C and clear.")],
        ]
    )


def _rule_based_agent() -> Agent:
    return Agent(
        name="Lab Assistant",
        instructions=(
            "Use the provided tools for arithmetic and weather questions. "
            "Answer in one short sentence."
        ),
        model=RuleBasedModel(),
        tools=[add_tool, multiply_tool, get_weather_tool],
    )


def _run_prompts(agent: Agent, prompts: list[str]) -> None:
    for prompt in prompts:
        result = Runner.run_sync(agent, prompt)
        print(f"> {prompt}")
        print(f"  {result.final_output}\n")


def _run_scripted_demo() -> None:
    _run_prompts(
        build_triage_agent(model=_offline_model()),
        ["What is 2 + 3?", "What's the weather in Tokyo?"],
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OpenAI Agents SDK lab demos")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="use the flexible offline rule-based model",
    )
    parser.add_argument("prompt", nargs="*", help="prompt for interactive or live mode")
    args = parser.parse_args(argv)

    use_openai = os.environ.get("AGENTS_LAB_USE_OPENAI") == "1"
    prompts = [" ".join(args.prompt)] if args.prompt else EXAMPLE_PROMPTS

    if use_openai:
        if not os.environ.get("OPENAI_API_KEY"):
            parser.error("AGENTS_LAB_USE_OPENAI=1 requires OPENAI_API_KEY")
        _run_prompts(build_triage_agent(), prompts)
    elif args.interactive or args.prompt:
        set_tracing_disabled(True)
        _run_prompts(_rule_based_agent(), prompts)
    else:
        set_tracing_disabled(True)
        _run_scripted_demo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
