#!/usr/bin/env python3
"""Parse Agents API SSE streams and dispatch side effects via shell helpers."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Any


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


@dataclass
class StreamState:
    session_id: str | None = None
    environment_id: str | None = None
    remote_url: str | None = None
    executor_started: bool = False
    turn_completed: bool = False
    turn_failed: bool = False
    failure_message: str | None = None


def run_script(script_name: str, *args: str) -> subprocess.CompletedProcess[str]:
    script_path = os.path.join(SCRIPT_DIR, script_name)
    return subprocess.run(
        ["bash", script_path, *args],
        env=os.environ.copy(),
        text=True,
        capture_output=True,
        check=False,
    )


def start_executor(state: StreamState) -> None:
    if state.executor_started or not state.environment_id or not state.remote_url:
        return
    result = run_script("start-executor.sh", state.remote_url, state.environment_id)
    if result.returncode != 0:
        sys.stderr.write(result.stderr or result.stdout)
        raise RuntimeError("Failed to start exec-server")
    sys.stderr.write(result.stderr)
    state.executor_started = True


def handle_required_actions(state: StreamState) -> None:
    if not state.session_id:
        return

    session = run_script("get-session.sh", state.session_id)
    if session.returncode != 0:
        sys.stderr.write(session.stderr or session.stdout)
        return

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
        handle.write(session.stdout)
        session_file = handle.name

    try:
        actions = run_script("handle-actions.sh", state.session_id, session_file)
        if actions.returncode != 0:
            sys.stderr.write(actions.stderr or actions.stdout)
        else:
            sys.stderr.write(actions.stderr)
    finally:
        os.unlink(session_file)


def extract_environment(payload: dict[str, Any], state: StreamState) -> None:
    environment = payload.get("environment") or payload.get("session", {}).get("environment")
    if isinstance(environment, dict):
        state.environment_id = environment.get("id") or state.environment_id
        state.remote_url = environment.get("remote_url") or state.remote_url

    data = payload.get("data") or {}
    if isinstance(data, dict):
        state.environment_id = data.get("environment_id") or state.environment_id
        connect = data.get("connect") or {}
        if isinstance(connect, dict):
            state.remote_url = connect.get("remote_url") or state.remote_url


def print_event(event: dict[str, Any], state: StreamState) -> None:
    event_type = event.get("type", "unknown")

    if event_type == "agent.session.created":
        session = event.get("session") or event.get("data") or {}
        if isinstance(session, dict):
            state.session_id = session.get("id") or state.session_id
            extract_environment(session, state)
        print(f"[session] created: {state.session_id}", flush=True)
        start_executor(state)
        return

    if "session" in event and isinstance(event["session"], dict):
        state.session_id = event["session"].get("id") or state.session_id
        extract_environment(event["session"], state)

    extract_environment(event, state)

    if event_type == "agent.session.environment.pending":
        print("[environment] pending executor connection", flush=True)
        start_executor(state)
        return

    if event_type == "agent.session.environment.connected":
        print("[environment] connected", flush=True)
        return

    if event_type == "agent.session.environment.failed":
        message = json.dumps(event, ensure_ascii=False)
        state.turn_failed = True
        state.failure_message = message
        print(f"[environment] failed: {message}", flush=True)
        return

    if event_type in {"agent.session.requires_action", "agent.session.action_required"}:
        print("[session] action required", flush=True)
        start_executor(state)
        handle_required_actions(state)
        return

    if event_type == "agent.session.turn.output_text.delta":
        delta = event.get("delta", "")
        sys.stdout.write(delta)
        sys.stdout.flush()
        return

    if event_type == "agent.session.turn.output_text.done":
        sys.stdout.write("\n")
        sys.stdout.flush()
        return

    if event_type == "agent.session.turn.tool_call.started":
        name = event.get("name")
        if not name and isinstance(event.get("tool"), dict):
            name = event["tool"].get("name")
        print(f"\n[tool] started: {name or 'unknown'}", flush=True)
        return

    if event_type == "agent.session.turn.tool_call.completed":
        print("[tool] completed", flush=True)
        return

    if event_type == "agent.session.turn.completed":
        turn = event.get("turn") or {}
        if turn.get("subagent_id") in (None, "", "null"):
            state.turn_completed = True
            print("\n[turn] completed", flush=True)
        return

    if event_type == "agent.session.turn.failed":
        turn = event.get("turn") or {}
        if turn.get("subagent_id") in (None, "", "null"):
            state.turn_failed = True
            error = turn.get("error") or {}
            state.failure_message = error.get("message") or json.dumps(event)
            print(f"\n[turn] failed: {state.failure_message}", flush=True)
        return

    if event_type == "agent.session.turn.cancelled":
        turn = event.get("turn") or {}
        if turn.get("subagent_id") in (None, "", "null"):
            state.turn_failed = True
            state.failure_message = "Turn cancelled"
            print("\n[turn] cancelled", flush=True)
        return

    if event_type == "agent.session.failed":
        state.turn_failed = True
        state.failure_message = json.dumps(event, ensure_ascii=False)
        print(f"\n[session] failed: {state.failure_message}", flush=True)
        return

    if event_type == "error":
        state.turn_failed = True
        error = event.get("error") or {}
        state.failure_message = error.get("message") or json.dumps(event)
        print(f"\n[error] {state.failure_message}", flush=True)
        return

    if event_type == "agent.session.idle":
        print("[session] idle", flush=True)
        return

    if event_type == "agent.session.in_progress":
        print("[session] in progress", flush=True)
        return

    print(f"[event] {event_type}", flush=True)


def parse_sse_stream(stream: Any, state: StreamState) -> None:
    data_lines: list[str] = []

    for raw_line in stream:
        line = raw_line.rstrip("\n")

        if line == "":
            if not data_lines:
                continue
            payload_raw = "\n".join(data_lines)
            data_lines = []
            if payload_raw == "[DONE]":
                break
            try:
                event = json.loads(payload_raw)
            except json.JSONDecodeError:
                print(f"[warn] non-json event: {payload_raw}", flush=True)
                continue
            print_event(event, state)
            if state.turn_completed or state.turn_failed:
                break
            continue

        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())


def main() -> int:
    state = StreamState()
    parse_sse_stream(sys.stdin, state)

    if state.turn_failed:
        return 1
    if not state.turn_completed:
        print(
            "[warn] Stream ended before root turn completed. "
            "Retrieve saved session items for the final state.",
            flush=True,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
