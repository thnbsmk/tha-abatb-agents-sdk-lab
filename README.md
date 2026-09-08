# tha-abatb-agents-sdk-lab

A hands-on lab for experimenting with the [OpenAI Agents SDK](https://github.com/openai/openai-agents-python).

It ships a small multi-agent setup — a **Triage Agent** that can use tools and
hand off to a **Weather Specialist** — plus a scripted offline model so the full
agent loop can run and be tested without an API key.

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (the install script installs it automatically)

## Setup

```bash
bash scripts/install.sh
```

This installs `uv` (if missing) and syncs the locked dependencies into `.venv`,
including dev tools (pytest, ruff).

## Run the demo

```bash
# Offline: runs against a scripted FakeModel (no network / no key needed)
uv run agents-lab-demo

# Real model: export a key first, then the same command uses OpenAI
export OPENAI_API_KEY=sk-...
uv run agents-lab-demo
```

The demo drives two flows end to end: an arithmetic request answered via the
`add` tool, and a weather request that hands off to the Weather Specialist,
which calls the `get_weather` tool.

## Lint and test

```bash
uv run ruff check .
uv run pytest
```

## Project layout

```
src/agents_lab/
  tools.py         # @function_tool examples (add, get_weather)
  lab_agents.py    # Triage Agent + Weather Specialist (with handoff)
  fake_model.py    # scripted offline Model for tests/demo
  demo.py          # runnable end-to-end demo
tests/             # offline unit + end-to-end agent tests
scripts/install.sh # idempotent environment setup
```
