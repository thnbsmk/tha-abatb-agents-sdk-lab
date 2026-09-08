# tha-abatb-agents-sdk-lab

A small lab for experimenting with the [OpenAI Agents SDK](https://openai.github.io/openai-agents-python/)
that runs **fully offline** — no API key or network required — so agents,
tools, and multi-turn tool calling can be exercised deterministically in tests
and demos.

## What's inside

- `src/agents_lab/tools.py` — example function tools (`add`, `multiply`, `get_weather`).
- `src/agents_lab/models.py` — local `Model` implementations for the SDK:
  - `ScriptedModel` replays a fixed script of responses (great for tests).
  - `RuleBasedModel` inspects the prompt and decides which tool to call.
- `src/agents_lab/demo.py` — a CLI that builds an `Agent` and runs it with `Runner`.
- `tests/` — end-to-end tests that run real `Agent`/`Runner` flows offline.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

In Cloud Agents this is done automatically by `.cursor/install.sh`.

## Run the demo

```bash
source .venv/bin/activate
agents-lab                    # runs a few built-in example prompts
agents-lab "what is 21 * 2?"  # run a single prompt
```

Example output:

```
> What is 2 + 3?
  The result is 5.0.
```

To run against a real OpenAI model instead of the offline model, set
`AGENTS_LAB_USE_OPENAI=1` and provide `OPENAI_API_KEY`.

## Lint and test

```bash
source .venv/bin/activate
ruff check .
pytest -q
```
