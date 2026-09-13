#!/usr/bin/env bash
# Execute pending function tools and submit results back to the session.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/agents-api.sh
source "${SCRIPT_DIR}/agents-api.sh"

handle_function_call() {
  local session_id="$1"
  local turn_id="$2"
  local call_id="$3"
  local name="$4"
  local arguments_json="$5"

  echo "[function] ${name}(${arguments_json})" >&2

  case "$name" in
    get_repository_info)
      local output
      output="$(jq -n \
        --arg workspace "${WORKSPACE_DIRECTORY:-/workspace/agensdk}" \
        '{
          workspace: $workspace,
          repository: "agents-sdk-lab",
          note: "Repository is checked out in the self-hosted workspace."
        }')"
      agents_api_submit_tool_result "$session_id" "$turn_id" "$call_id" true "$output"
      ;;
    *)
      agents_api_submit_tool_result \
        "$session_id" "$turn_id" "$call_id" false "" \
        "No application handler is registered for function '${name}'. Extend lib/handle-functions.sh."
      ;;
  esac
}

handle_required_actions() {
  local session_id="$1"
  local session_json="$2"

  local actions
  actions="$(jq -c '.required_actions // []' <<<"$session_json")"
  local count
  count="$(jq 'length' <<<"$actions")"

  if [[ "$count" == "0" ]]; then
    return 0
  fi

  echo "[session] Handling ${count} required action(s)" >&2

  jq -c '.[]' <<<"$actions" | while IFS= read -r action; do
    local action_type
    action_type="$(jq -r '.type' <<<"$action")"

    case "$action_type" in
      function_call)
        handle_function_call \
          "$session_id" \
          "$(jq -r '.turn_id' <<<"$action")" \
          "$(jq -r '.call_id' <<<"$action")" \
          "$(jq -r '.name' <<<"$action")" \
          "$(jq -c '.arguments // {}' <<<"$action")"
        ;;
      environment_connection)
        echo "[session] Environment connection still required; ensure exec-server is running." >&2
        ;;
      *)
        echo "[session] Unsupported required action type: ${action_type}" >&2
        ;;
    esac
  done
}
