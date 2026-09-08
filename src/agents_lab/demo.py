"""Runnable end-to-end demo for the Agents SDK lab.

Run it with::

    uv run agents-lab-demo
    # or
    uv run python -m agents_lab.demo

Behavior:

* If ``OPENAI_API_KEY`` is set, the demo runs the triage agent against a real
  OpenAI model and prints the model's answers.
* Otherwise it falls back to a scripted :class:`FakeModel` so the full
  agent -> tool-call -> handoff -> final-answer flow still runs end to end
  offline (useful in CI and for validating the dev environment).
"""

from __future__ import annotations

import json
import os

from agents import Handoff, Runner

from .fake_model import FakeModel, text_message, tool_call
from .lab_agents import build_triage_agent, build_weather_specialist


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


def main() -> None:
    use_real = bool(os.environ.get("OPENAI_API_KEY"))
    if not use_real:
        # No API key -> disable the SDK's network trace export to avoid noise.
        from agents import set_tracing_disabled

        set_tracing_disabled(True)
    model = None if use_real else _offline_model()
    mode = "REAL OpenAI model" if use_real else "offline FakeModel"
    print(f"== Agents SDK lab demo ({mode}) ==\n")

    agent = build_triage_agent(model=model)

    prompt1 = "What is 2 + 3?"
    print(f"[user] {prompt1}")
    result1 = Runner.run_sync(agent, prompt1)
    print(f"[agent] {result1.final_output}\n")

    prompt2 = "What's the weather in Tokyo?"
    print(f"[user] {prompt2}")
    result2 = Runner.run_sync(agent, prompt2)
    print(f"[agent] {result2.final_output}")
    print(f"[last agent] {result2.last_agent.name}")


if __name__ == "__main__":
    main()
