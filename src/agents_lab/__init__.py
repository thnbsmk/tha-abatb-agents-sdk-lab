"""agents_lab: a minimal, self-contained lab for tool-calling agents."""

from __future__ import annotations

from .agent import Agent
from .demo import build_demo_agent, calculator, echo, safe_eval
from .models import FinalAnswer, Message, MockModel, Model, ModelAction, ToolCall
from .runner import Runner, RunResult, Step
from .tools import Tool, tool

__all__ = [
    "Agent",
    "FinalAnswer",
    "Message",
    "MockModel",
    "Model",
    "ModelAction",
    "RunResult",
    "Runner",
    "Step",
    "Tool",
    "ToolCall",
    "build_demo_agent",
    "calculator",
    "echo",
    "safe_eval",
    "tool",
]

__version__ = "0.1.0"
