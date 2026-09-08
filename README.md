# tha-abatb-agents-sdk-lab

A minimal, self-contained lab for experimenting with **tool-calling agents** in Python.

It implements the core pieces of an "agents SDK" with zero runtime dependencies, so it
runs end-to-end offline (no API keys required):

- `Tool` / `@tool` — wrap a plain function as a tool an agent can call.
- `Model` — decides the next action (call a tool or answer). `MockModel` is a
  deterministic, offline default.
- `Agent` — a name, instructions, tools, and a model.
- `Runner` — drives the loop: model → tool → observation → … → final answer.

## Requirements

- Python 3.10+

## Setup

```bash
pip install -e ".[dev]"
```

## Run the demo

```bash
agents-lab "Compute (6 * 7) + 3"        # -> The calculator result is 45.0.
agents-lab --trace "Compute (6 * 7) + 3" # show each tool call
python -m agents_lab "hello there"       # -> The echo result is hello there.
```

## Use it in code

```python
from agents_lab import Runner, build_demo_agent

result = Runner.run(build_demo_agent(), "Compute (6 * 7) + 3")
print(result.final_output)  # The calculator result is 45.0.
```

## Development

```bash
ruff check .          # lint
mypy                  # type-check (config in pyproject.toml)
pytest                # run tests
```
