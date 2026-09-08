"""The :class:`Agent`: a name, instructions, tools, and the model that drives it."""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import MockModel, Model
from .tools import Tool


@dataclass
class Agent:
    """An agent configuration consumed by :class:`agents_lab.runner.Runner`."""

    name: str
    instructions: str = ""
    tools: list[Tool] = field(default_factory=list)
    model: Model = field(default_factory=MockModel)

    @property
    def tool_map(self) -> dict[str, Tool]:
        """Tools keyed by name for quick lookup during a run."""
        return {t.name: t for t in self.tools}
