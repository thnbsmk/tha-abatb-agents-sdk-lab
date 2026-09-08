#!/usr/bin/env bash
# Idempotent Cloud Agent bootstrap for the Agents SDK lab.
# Creates a project virtualenv at .venv and installs the package (with dev deps).
set -euo pipefail

cd "$(dirname "$0")/.."

# The default image's system Python may lack the `ensurepip`/venv module.
if ! python3 -c "import ensurepip" >/dev/null 2>&1; then
  sudo apt-get update -qq
  sudo apt-get install -y -qq python3-venv
fi

if [ ! -x ".venv/bin/python" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
. .venv/bin/activate

python -m pip install --upgrade pip
pip install -e ".[dev]"

echo "agents-sdk-lab environment ready. Activate with: source .venv/bin/activate"
