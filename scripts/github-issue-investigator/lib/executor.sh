#!/usr/bin/env bash
# Manage the Codex exec-server for a self-hosted Agents API environment.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="${SCRIPT_DIR}/../.run"
PID_FILE="${RUN_DIR}/exec-server.pid"
LOG_FILE="${RUN_DIR}/exec-server.log"

: "${WORKSPACE_DIRECTORY:=/workspace/agensdk}"
: "${CODEX_BIN:=/workspace/.codex-cli/node_modules/.bin/codex}"

executor_require_environment_key() {
  if [[ -z "${OPENAI_ENVIRONMENT_KEY:-}" ]]; then
    echo "OPENAI_ENVIRONMENT_KEY is required for the Codex exec-server." >&2
    echo "Create a restricted environment key in the OpenAI project Agents tab." >&2
    return 1
  fi
}

executor_is_running() {
  [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

executor_stop() {
  if executor_is_running; then
    local pid
    pid="$(cat "$PID_FILE")"
    echo "[executor] Stopping exec-server (pid ${pid})" >&2
    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
}

executor_start() {
  local remote_url="$1"
  local environment_id="$2"

  executor_require_environment_key

  if [[ -z "$remote_url" || -z "$environment_id" ]]; then
    echo "[executor] remote_url and environment_id are required." >&2
    return 1
  fi

  if ! command -v "$CODEX_BIN" >/dev/null 2>&1; then
    echo "[executor] Codex CLI not found at ${CODEX_BIN}." >&2
    echo "[executor] Install with: npm install @openai/codex --prefix /workspace/.codex-cli" >&2
    return 1
  fi

  mkdir -p "$RUN_DIR"
  executor_stop

  echo "[executor] Starting exec-server for ${environment_id}" >&2
  echo "[executor] Workspace: ${WORKSPACE_DIRECTORY}" >&2
  echo "[executor] Remote URL: ${remote_url}" >&2

  (
    cd "$WORKSPACE_DIRECTORY"
    export CODEX_API_KEY="$OPENAI_ENVIRONMENT_KEY"
    exec "$CODEX_BIN" exec-server \
      --remote "$remote_url" \
      --environment-id "$environment_id"
  ) >>"$LOG_FILE" 2>&1 &

  echo $! >"$PID_FILE"
  sleep 1

  if ! executor_is_running; then
    echo "[executor] exec-server failed to start. Recent log output:" >&2
    tail -n 40 "$LOG_FILE" >&2 || true
    return 1
  fi

  echo "[executor] exec-server running (pid $(cat "$PID_FILE"), log: ${LOG_FILE})" >&2
}
