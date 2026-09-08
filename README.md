# tha-abatb-agents-sdk-lab

A hands-on lab for experimenting with the
[OpenAI Agents SDK](https://github.com/openai/openai-agents-python).

The project combines the strongest parts of the repository's original
experiments in one coherent package:

- a **Triage Agent** that can use arithmetic tools and hand off to a
  **Weather Specialist**;
- a scripted `FakeModel` for deterministic tool and handoff tests;
- a flexible `RuleBasedModel` for trying custom prompts offline;
- an optional live OpenAI mode.

Offline modes do not require an API key or network access.

## Requirements

- Python >= 3.10
- [uv](https://docs.astral.sh/uv/) (installed automatically by the setup script)

## Setup

```bash
bash scripts/install.sh
```

This installs `uv` when needed and syncs the locked dependencies into `.venv`,
including pytest and Ruff.

## Run the demo

```bash
# Scripted offline demo: arithmetic tool call plus specialist handoff
uv run agents-lab

# Flexible offline mode with a custom prompt
uv run agents-lab --interactive "what is 21 * 2?"
```

To use a live OpenAI model, opt in explicitly and provide the key through your
environment. Never commit the key or an `.env` file.

```bash
export AGENTS_LAB_USE_OPENAI=1
export OPENAI_API_KEY=your-key
uv run agents-lab "What's the weather in Bangkok?"
```

## Lint and test

```bash
uv run ruff check .
uv run pytest
```

## Project layout

```
src/agents_lab/
  tools.py         # @function_tool examples (add, multiply, get_weather)
  lab_agents.py    # Triage Agent + Weather Specialist (with handoff)
  fake_model.py    # scripted offline model for deterministic flows
  models.py        # flexible offline rule-based model
  demo.py          # runnable end-to-end demo
tests/             # offline unit + end-to-end agent tests
scripts/install.sh # idempotent environment setup
```
