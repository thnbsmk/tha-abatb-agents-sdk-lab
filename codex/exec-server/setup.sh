#!/usr/bin/env bash
# One-time bootstrap for a Cursor Remote / self-hosted Codex executor host.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${WORKSPACE_DIRECTORY:=/workspace/agensdk}"
: "${CODEX_INSTALL_DIR:=/workspace/.codex-cli}"
: "${AGENSDK_REPO:=https://github.com/thnbsmk/tha-abatb-agents-sdk-lab.git}"

echo "[setup] Workspace target: ${WORKSPACE_DIRECTORY}"
echo "[setup] Codex install dir: ${CODEX_INSTALL_DIR}"

if [[ ! -d "${WORKSPACE_DIRECTORY}" ]]; then
  echo "[setup] Cloning agents-sdk-lab into ${WORKSPACE_DIRECTORY}"
  git clone --depth 1 "${AGENSDK_REPO}" "${WORKSPACE_DIRECTORY}"
else
  echo "[setup] Workspace already exists: ${WORKSPACE_DIRECTORY}"
fi

if [[ ! -x "${CODEX_INSTALL_DIR}/node_modules/.bin/codex" ]]; then
  echo "[setup] Installing Codex CLI"
  npm install @openai/codex --prefix "${CODEX_INSTALL_DIR}"
fi

export CODEX_BIN="${CODEX_INSTALL_DIR}/node_modules/.bin/codex"
echo "[setup] Codex CLI: ${CODEX_BIN}"
"${CODEX_BIN}" --version || true

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
  echo "[setup] Created ${ROOT_DIR}/.env — add OPENAI_ENVIRONMENT_KEY before connecting."
fi

echo "[setup] Done."
