"""The run loop that connects an :class:`~agents_lab.agent.Agent` to its tools."""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent import Agent
from .models import FinalAnswer, Message, ToolCall


@dataclass
class Step:
    """One iteration of the loop: the model action and any tool observation."""

    action: ToolCall | FinalAnswer
    observation: str | None = None


@dataclass
class RunResult:
    """The outcome of a run: the final text and the full trace of steps."""

    final_output: str
    steps: list[Step] = field(default_factory=list)


class Runner:
    """Executes an agent against a user input until it produces a final answer."""

    @staticmethod
    def run(agent: Agent, user_input: str, *, max_steps: int = 10) -> RunResult:
        conversation: list[Message] = [Message(role="user", content=user_input)]
        steps: list[Step] = []
        tools = agent.tool_map

        for _ in range(max_steps):
            action = agent.model.decide(agent, conversation)

            if isinstance(action, FinalAnswer):
                conversation.append(Message(role="assistant", content=action.content))
                steps.append(Step(action=action))
                return RunResult(final_output=action.content, steps=steps)

            tool = tools.get(action.tool)
            if tool is None:
                observation = f"Error: unknown tool '{action.tool}'"
            else:
                observation = tool.invoke(action.arguments)

            conversation.append(
                Message(role="assistant", content=f"call {action.tool}({action.arguments})")
            )
            conversation.append(Message(role="tool", content=observation, tool_name=action.tool))
            steps.append(Step(action=action, observation=observation))

        raise RuntimeError(f"Agent exceeded max_steps={max_steps} without finishing")
