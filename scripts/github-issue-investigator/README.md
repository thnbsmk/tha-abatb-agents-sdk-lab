# GitHub Issue Investigation Agent (Agents API)

Runnable shell application that starts an [OpenAI Agents API](https://developers.openai.com/api/docs/guides/agents-api/overview) session using the saved agent **GitHub issue investigation agent**, applies session overrides for model/instructions/reasoning/text settings, connects a **self-hosted** Codex executor, sends an initial user message, and streams session output/events via `curl`.

## Prerequisites

1. **Node.js 22+** (for the optional Codex CLI install used by the executor)
2. **`curl`**, **`jq`**, **`python3`**
3. **OpenAI project** `proj_Kbc70ouR70glbq4U3fvrhBTp`
4. **Saved agent** `agent_5ff88ea0ea894e468128481c5e08c233c55b20d741264d78b8`
5. **Workspace checkout** at `/workspace/agensdk` (symlink to this repo is fine)

## Credentials

| Variable | Where it runs | Purpose |
| --- | --- | --- |
| `OPENAI_API_KEY` | Your machine / app host | Create sessions, stream events, submit function results |
| `OPENAI_ENVIRONMENT_KEY` | Inside the self-hosted workspace | Start `codex exec-server` only |

Create keys in the OpenAI Platform project:

- **Application key**: `api.agents.read`, `api.agents.write`, `api.responses.write`
- **Environment key**: `api.agents.environments.connect` only

Copy `config.env.example` and export the values before running.

## Cursor Remote quick path

For the bank-linked Cursor Remote terminal (not this chat sandbox), use the
dedicated bootstrap package:

```bash
git clone https://github.com/thnbsmk/tha-abatb-agents-sdk-lab.git /workspace/agensdk
cd /workspace/agensdk/codex/exec-server
./setup.sh && cp .env.example .env
# edit .env, then:
./connect.sh
```

See `codex/exec-server/README.md` for details.

## One-time setup

```bash
# From the repository root
npm install @openai/codex --prefix .codex-cli

# Ensure the workspace path exists for the self-hosted environment
ln -sfn /workspace /workspace/agensdk

cp scripts/github-issue-investigator/config.env.example .env.agents
# Edit .env.agents with your keys, then:
set -a && source .env.agents && set +a
```

## Run an investigation

```bash
# Default sample issue message
npm run agents:github-issue

# Or directly:
./scripts/github-issue-investigator/run.sh

# Custom issue text
./scripts/github-issue-investigator/run.sh --message-file ./my-issue.md
```

The script:

1. Builds a session payload with `agent_id` plus session overrides from `agent-overrides.json`
2. Calls `POST /v1/agents/sessions` with `stream: true` using `curl`
3. Starts `codex exec-server` when the API returns environment connection details
4. Streams deltas, tool activity, environment status, and turn outcomes
5. Handles pending function tools via `required_actions` (extend `lib/handle-functions.sh`)

## What gets overridden per session

Only these fields are overridden; all other saved agent settings are preserved:

- `model`: `gpt-6-astra`
- `instructions`: GitHub issue investigation workflow
- `reasoning`: `{ "effort": "medium", "summary": "auto" }`
- `text`: `{ "format": { "type": "text" }, "verbosity": "medium" }`

## Manual API examples (`curl`)

Create a session (non-streaming retrieve of session object):

```bash
curl -sS https://api.openai.com/v1/agents/sessions \
  -H "OpenAI-Beta: agents=v1" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Project: $OPENAI_PROJECT_ID" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

Stream events for an existing session:

```bash
curl -N "https://api.openai.com/v1/agents/sessions/$SESSION_ID/events?stream=true" \
  -H "OpenAI-Beta: agents=v1" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "OpenAI-Project: $OPENAI_PROJECT_ID" \
  -H "Accept: text/event-stream"
```

Start the executor inside the workspace:

```bash
cd /workspace/agensdk
CODEX_API_KEY="$OPENAI_ENVIRONMENT_KEY" \
  /workspace/.codex-cli/node_modules/.bin/codex exec-server \
    --remote "$REMOTE_URL" \
    --environment-id "$ENVIRONMENT_ID"
```

## Troubleshooting

- **`OPENAI_API_KEY is required`**: export your application key before running.
- **`OPENAI_ENVIRONMENT_KEY is required`**: create a restricted environment key in the project Agents tab.
- **`environment.pending` never connects**: confirm outbound access to `api.openai.com` and `wss://codex-cloud-environments.chatgpt.com`.
- **Function tool errors**: add handlers in `lib/handle-functions.sh` for tools defined on the saved agent.
- **Executor logs**: `scripts/github-issue-investigator/.run/exec-server.log`
