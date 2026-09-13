#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/agents-api.sh
source "${SCRIPT_DIR}/agents-api.sh"
agents_api_get_session "$1"
