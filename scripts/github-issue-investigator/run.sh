#!/usr/bin/env bash
# Start a GitHub issue investigation session via the OpenAI Agents HTTP API.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# shellcheck source=lib/agents-api.sh
source "${SCRIPT_DIR}/lib/agents-api.sh"
# shellcheck source=lib/executor.sh
source "${SCRIPT_DIR}/lib/executor.sh"

: "${OPENAI_PROJECT_ID:=proj_Kbc70ouR70glbq4U3fvrhBTp}"
: "${AGENT_ID:=agent_5ff88ea0ea894e468128481c5e08c233c55b20d741264d78b8}"
: "${AGENT_NAME:=GitHub issue investigation agent}"
: "${WORKSPACE_DIRECTORY:=/workspace/agensdk}"
: "${INITIAL_MESSAGE_FILE:=${SCRIPT_DIR}/sample-issue.md}"
: "${OPENAI_API_BASE:=https://api.openai.com/v1}"
: "${KEEP_EXECUTOR_RUNNING:=false}"

export OPENAI_PROJECT_ID AGENT_ID AGENT_NAME WORKSPACE_DIRECTORY OPENAI_API_BASE AGENTS_API_BETA_HEADER
export CODEX_BIN="${CODEX_BIN:-/workspace/.codex-cli/node_modules/.bin/codex}"

usage() {
  cat <<'EOF'
Usage: ./run.sh [options]

Starts an Agents API session for the saved "GitHub issue investigation agent",
connects a self-hosted Codex exec-server, sends an initial user message, and
streams session events to stdout.

Options:
  -m, --message-file PATH   Initial user message file (default: sample-issue.md)
  -w, --workspace PATH      Self-hosted workspace directory (default: /workspace/agensdk)
  -k, --keep-executor       Leave exec-server running after the script exits
  -h, --help                Show this help

Required environment variables:
  OPENAI_API_KEY            Application API key (api.agents.read/write, api.responses.write)
  OPENAI_ENVIRONMENT_KEY    Restricted environment key for codex exec-server

Optional environment variables:
  OPENAI_PROJECT_ID         Default: proj_Kbc70ouR70glbq4U3fvrhBTp
  AGENT_ID                  Saved agent definition ID
  CODEX_BIN                 Path to codex CLI (default: /workspace/.codex-cli/.../codex)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -m|--message-file)
      INITIAL_MESSAGE_FILE="$2"
      shift 2
      ;;
    -w|--workspace)
      WORKSPACE_DIRECTORY="$2"
      shift 2
      ;;
    -k|--keep-executor)
      KEEP_EXECUTOR_RUNNING=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command curl
require_command jq
require_command python3

agents_api_require_key
executor_require_environment_key

if [[ ! -f "$INITIAL_MESSAGE_FILE" ]]; then
  echo "Initial message file not found: ${INITIAL_MESSAGE_FILE}" >&2
  exit 1
fi

if [[ ! -d "$WORKSPACE_DIRECTORY" ]]; then
  echo "Workspace directory not found: ${WORKSPACE_DIRECTORY}" >&2
  echo "Create it or symlink your project checkout, for example:" >&2
  echo "  ln -sfn /workspace ${WORKSPACE_DIRECTORY}" >&2
  exit 1
fi

if [[ ! -x "${SCRIPT_DIR}/lib/stream-events.py" ]]; then
  chmod +x "${SCRIPT_DIR}/lib/"*.sh "${SCRIPT_DIR}/lib/stream-events.py" "${SCRIPT_DIR}/run.sh" 2>/dev/null || true
fi

INITIAL_MESSAGE="$(cat "$INITIAL_MESSAGE_FILE")"
PAYLOAD_FILE="$(mktemp)"
SESSION_LOG="$(mktemp)"
trap 'rm -f "$PAYLOAD_FILE"; [[ "$KEEP_EXECUTOR_RUNNING" == true ]] || executor_stop' EXIT

agents_api_build_session_payload \
  "${SCRIPT_DIR}/agent-overrides.json" \
  "$INITIAL_MESSAGE" \
  "$WORKSPACE_DIRECTORY" \
  "$AGENT_ID" >"$PAYLOAD_FILE"

echo "Project:        ${OPENAI_PROJECT_ID}" >&2
echo "Agent:          ${AGENT_NAME}" >&2
echo "Agent ID:       ${AGENT_ID}" >&2
echo "Workspace:      ${WORKSPACE_DIRECTORY}" >&2
echo "Message file:   ${INITIAL_MESSAGE_FILE}" >&2
echo "Creating session and streaming events..." >&2
echo >&2

set +e
curl --no-buffer --fail-with-body "${OPENAI_API_BASE}/agents/sessions" \
  -H "OpenAI-Beta: ${AGENTS_API_BETA_HEADER}" \
  -H "Authorization: Bearer ${OPENAI_API_KEY}" \
  -H "OpenAI-Project: ${OPENAI_PROJECT_ID}" \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d @"${PAYLOAD_FILE}" \
  | tee "$SESSION_LOG" \
  | python3 "${SCRIPT_DIR}/lib/stream-events.py"
STREAM_EXIT=$?
set -e

if [[ "$STREAM_EXIT" -ne 0 ]]; then
  echo >&2
  echo "Session stream exited with status ${STREAM_EXIT}." >&2
  if [[ -s "$SESSION_LOG" ]]; then
    SESSION_ID="$(grep -Eo 'sess_[A-Za-z0-9]+' "$SESSION_LOG" | head -n1 || true)"
    if [[ -n "$SESSION_ID" ]]; then
      echo "Session ID: ${SESSION_ID}" >&2
      echo "Retrieve items with:" >&2
      echo "  OPENAI_API_KEY=... curl -sS '${OPENAI_API_BASE}/agents/sessions/${SESSION_ID}/items?order=asc&limit=100' \\" >&2
      echo "    -H 'OpenAI-Beta: ${AGENTS_API_BETA_HEADER}' -H 'Authorization: Bearer \$OPENAI_API_KEY' -H 'OpenAI-Project: ${OPENAI_PROJECT_ID}' | jq ." >&2
    fi
  fi
  exit "$STREAM_EXIT"
fi

echo >&2
echo "Investigation session completed successfully." >&2
exit 0
