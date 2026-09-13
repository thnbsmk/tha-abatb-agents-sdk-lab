#!/usr/bin/env bash
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

fail=0

if [[ -d "${WORKSPACE_DIRECTORY}" ]]; then
  echo "ok  workspace ${WORKSPACE_DIRECTORY}"
else
  echo "missing workspace ${WORKSPACE_DIRECTORY}"
  fail=1
fi

if [[ -x "${CODEX_BIN}" ]] || command -v codex >/dev/null 2>&1; then
  echo "ok  codex cli"
else
  echo "missing codex cli (${CODEX_BIN})"
  fail=1
fi

if [[ -n "${OPENAI_ENVIRONMENT_KEY:-}" ]]; then
  echo "ok  OPENAI_ENVIRONMENT_KEY"
else
  echo "missing OPENAI_ENVIRONMENT_KEY"
  fail=1
fi

if [[ -n "${REMOTE_URL:-}" && -n "${ENVIRONMENT_ID:-}" ]]; then
  echo "ok  REMOTE_URL + ENVIRONMENT_ID"
else
  echo "warn REMOTE_URL / ENVIRONMENT_ID not set (required only when connecting)"
fi

exit "$fail"
