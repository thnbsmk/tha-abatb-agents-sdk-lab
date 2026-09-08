"""Command-line entry point: run the demo agent against a prompt.

Examples::

    agents-lab "Compute (6 * 7) + 3"
    python -m agents_lab --trace "hello there"
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .demo import build_demo_agent
from .models import ToolCall
from .runner import Runner


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="agents-lab", description=__doc__)
    parser.add_argument(
        "prompt",
        nargs="*",
        help="The prompt to send to the demo agent.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print each step (tool calls and observations) the agent takes.",
    )
    args = parser.parse_args(argv)

    prompt = " ".join(args.prompt).strip() or "Compute (6 * 7) + 3"
    agent = build_demo_agent()
    result = Runner.run(agent, prompt)

    print(f"> {prompt}")
    if args.trace:
        for i, step in enumerate(result.steps, start=1):
            action = step.action
            if isinstance(action, ToolCall):
                print(f"  [{i}] tool {action.tool}({action.arguments}) -> {step.observation}")
            else:
                print(f"  [{i}] final")
    print(result.final_output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
