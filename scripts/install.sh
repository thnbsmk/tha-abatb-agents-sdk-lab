#!/usr/bin/env bash
# Idempotent dependency setup for the agents-sdk-lab Cloud Agent environment.
# Installs uv (if needed) and syncs the locked Python dependencies.
set -euo pipefail

# Ensure uv (fast Python package manager) is available.
if ! command -v uv >/dev/null 2>&1; then
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | env INSTALLER_NO_MODIFY_PATH=1 sh
fi
export PATH="$HOME/.local/bin:$PATH"

uv --version

# Create/sync the project virtual environment from the lockfile, including dev
# dependencies. --frozen fails if the lockfile is stale; fall back to a normal
# sync (which refreshes the lock) so setup still converges.
if ! uv sync --frozen --extra dev; then
  echo "Lockfile out of date; running a non-frozen sync to refresh it."
  uv sync --extra dev
fi

echo "install.sh completed successfully."
