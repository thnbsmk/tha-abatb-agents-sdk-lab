#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/executor.sh
source "${SCRIPT_DIR}/executor.sh"
executor_start "$1" "$2"
