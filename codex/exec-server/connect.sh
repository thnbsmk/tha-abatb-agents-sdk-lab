#!/usr/bin/env bash
# Connect this machine to an OpenAI Agents API / ChatGPT self-hosted session.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "${ROOT_DIR}/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.env"
  set +a
fi

: "${WORKSPACE_DIRECTORY:=/workspace/agensdk}"
: "${CODEX_BIN:=/workspace/.codex-cli/node_modules/.bin/codex}"

usage() {
  cat <<'EOF'
Usage: ./connect.sh [--remote URL] [--environment-id ID]

Starts codex exec-server and keeps it running for a ChatGPT / Agents session.

Environment (or .env):
  OPENAI_ENVIRONMENT_KEY   Restricted environment key
  WORKSPACE_DIRECTORY      Default: /workspace/agensdk
  REMOTE_URL               From the active session
  ENVIRONMENT_ID           From the active session

Example:
  REMOTE_URL='https://api.openai.com/v1/agents/api/connect/rt_xxx' \
  ENVIRONMENT_ID='ccarenv_xxx' \
  ./connect.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE_URL="$2"
      shift 2
      ;;
    --environment-id)
      ENVIRONMENT_ID="$2"
      shift 2
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

if [[ -z "${OPENAI_ENVIRONMENT_KEY:-}" ]]; then
  echo "OPENAI_ENVIRONMENT_KEY is required." >&2
  exit 1
fi

if [[ -z "${REMOTE_URL:-}" || -z "${ENVIRONMENT_ID:-}" ]]; then
  echo "REMOTE_URL and ENVIRONMENT_ID are required." >&2
  usage >&2
  exit 1
fi

if [[ ! -d "${WORKSPACE_DIRECTORY}" ]]; then
  echo "Workspace not found: ${WORKSPACE_DIRECTORY}" >&2
  echo "Run ./setup.sh first." >&2
  exit 1
fi

if [[ ! -x "${CODEX_BIN}" ]]; then
  if command -v codex >/dev/null 2>&1; then
    CODEX_BIN="$(command -v codex)"
  else
    echo "Codex CLI not found. Run ./setup.sh first." >&2
    exit 1
  fi
fi

echo "[connect] workspace: ${WORKSPACE_DIRECTORY}"
echo "[connect] environment: ${ENVIRONMENT_ID}"
echo "[connect] remote: ${REMOTE_URL}"
echo "[connect] starting exec-server (leave this terminal open)..."

cd "${WORKSPACE_DIRECTORY}"
export CODEX_API_KEY="${OPENAI_ENVIRONMENT_KEY}"
exec "${CODEX_BIN}" exec-server \
  --remote "${REMOTE_URL}" \
  --environment-id "${ENVIRONMENT_ID}"
