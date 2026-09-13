#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/handle-functions.sh
source "${SCRIPT_DIR}/handle-functions.sh"

session_id="$1"
session_file="$2"
session_json="$(cat "$session_file")"
handle_required_actions "$session_id" "$session_json"
