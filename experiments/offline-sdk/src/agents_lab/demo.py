"""Command-line demo that runs an Agents SDK agent fully offline.

Usage::

    agents-lab                      # runs a few built-in example prompts
    agents-lab "what is 21 * 2?"    # run a single prompt

By default the demo uses :class:`agents_lab.models.RuleBasedModel`, so it needs
no API key or network. Set ``AGENTS_LAB_USE_OPENAI=1`` (and ``OPENAI_API_KEY``)
to run against a real OpenAI model instead.
"""

from __future__ import annotations

import argparse
import os
import sys

from agents import Agent, Runner, set_tracing_disabled

from .models import RuleBasedModel
from .tools import add, get_weather, multiply

INSTRUCTIONS = (
    "You are a concise assistant. Use the provided tools to do arithmetic and "
    "to look up the weather. Answer in one short sentence."
)

EXAMPLE_PROMPTS = [
    "What is 2 + 3?",
    "Please multiply 21 times 2.",
    "What's the weather in Tokyo?",
]


def build_agent() -> Agent:
    """Construct the lab agent, choosing an offline or OpenAI model."""
    use_openai = os.environ.get("AGENTS_LAB_USE_OPENAI") == "1"
    if not use_openai:
        set_tracing_disabled(True)
    model = None if use_openai else RuleBasedModel()
    return Agent(
        name="Lab Assistant",
        instructions=INSTRUCTIONS,
        model=model,
        tools=[add, multiply, get_weather],
    )


def run_prompt(agent: Agent, prompt: str) -> str:
    """Run a single prompt synchronously and return the final text output."""
    result = Runner.run_sync(agent, prompt)
    return result.final_output


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline Agents SDK lab demo.")
    parser.add_argument("prompt", nargs="*", help="A single prompt to run.")
    args = parser.parse_args(argv)

    agent = build_agent()
    prompts = [" ".join(args.prompt)] if args.prompt else EXAMPLE_PROMPTS

    for prompt in prompts:
        answer = run_prompt(agent, prompt)
        print(f"> {prompt}")
        print(f"  {answer}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
