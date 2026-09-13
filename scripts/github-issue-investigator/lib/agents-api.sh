#!/usr/bin/env bash
# Shared curl helpers for the OpenAI Agents HTTP API.
set -euo pipefail

: "${OPENAI_API_BASE:=https://api.openai.com/v1}"
: "${OPENAI_PROJECT_ID:=proj_Kbc70ouR70glbq4U3fvrhBTp}"
: "${AGENTS_API_BETA_HEADER:=agents=v1}"

agents_api_require_key() {
  if [[ -z "${OPENAI_API_KEY:-}" ]]; then
    echo "OPENAI_API_KEY is required (application key with api.agents.read/write)." >&2
    return 1
  fi
}

agents_api_curl() {
  local method="$1"
  local path="$2"
  shift 2

  agents_api_require_key

  curl -sS --fail-with-body -X "$method" "${OPENAI_API_BASE}${path}" \
    -H "OpenAI-Beta: ${AGENTS_API_BETA_HEADER}" \
    -H "Authorization: Bearer ${OPENAI_API_KEY}" \
    -H "OpenAI-Project: ${OPENAI_PROJECT_ID}" \
    "$@"
}

agents_api_get_session() {
  local session_id="$1"
  agents_api_curl GET "/agents/sessions/${session_id}"
}

agents_api_list_items() {
  local session_id="$1"
  agents_api_curl GET "/agents/sessions/${session_id}/items?order=asc&limit=100"
}

agents_api_post_events() {
  local session_id="$1"
  local payload="$2"
  agents_api_curl POST "/agents/sessions/${session_id}/events" \
    -H "Content-Type: application/json" \
    -d "$payload"
}

agents_api_submit_tool_result() {
  local session_id="$1"
  local turn_id="$2"
  local call_id="$3"
  local success="$4"
  local output="${5:-}"
  local error="${6:-}"

  local payload
  if [[ "$success" == "true" ]]; then
    payload="$(jq -n \
      --arg turn_id "$turn_id" \
      --arg call_id "$call_id" \
      --arg output "$output" \
      '{
        events: [{
          type: "agent.session.input.tool_result",
          turn_id: $turn_id,
          call_id: $call_id,
          success: true,
          output: $output
        }]
      }')"
  else
    payload="$(jq -n \
      --arg turn_id "$turn_id" \
      --arg call_id "$call_id" \
      --arg error "$error" \
      '{
        events: [{
          type: "agent.session.input.tool_result",
          turn_id: $turn_id,
          call_id: $call_id,
          success: false,
          error: $error
        }]
      }')"
  fi

  agents_api_post_events "$session_id" "$payload"
}

agents_api_build_session_payload() {
  local overrides_file="$1"
  local input_text="$2"
  local workspace_dir="$3"
  local agent_id="$4"

  jq -n \
    --arg agent_id "$agent_id" \
    --slurpfile overrides "$overrides_file" \
    --arg input_text "$input_text" \
    --arg workspace_dir "$workspace_dir" \
    '{
      agent_id: $agent_id,
      agent: $overrides[0].agent,
      environment: {
        type: "self_hosted",
        workspace_directory: $workspace_dir
      },
      input: $input_text,
      stream: true
    }'
}
