#!/usr/bin/env python3
"""
Claw Office UI - AI Office Bridge v2

Unified bridge script for pushing real-time AI agent status.
Supports: Claude Code (hooks), Codex CLI (JSONL stream), Gemini CLI (hooks).

Usage:
  # Claude Code hook mode
  python3 ai-office-bridge-v2.py claude-code hook < event.json

  # Codex CLI JSONL stream mode
  codex exec --json "task" 2>&1 | python3 ai-office-bridge-v2.py codex --stream

  # Gemini CLI hook mode
  python3 ai-office-bridge-v2.py gemini hook < event.json

  # Manual state push
  python3 ai-office-bridge-v2.py manual writing "Editing files"

  # Register new agent
  python3 ai-office-bridge-v2.py register --name "My Agent" --source "claude-code"

Environment:
  STAR_OFFICE_URL       - Office server URL (default: http://127.0.0.1:19000)
  STAR_OFFICE_AGENT_ID  - Pre-registered agent ID (optional)
  STAR_OFFICE_VERBOSE   - Enable debug output (1)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error

BASE_URL = os.environ.get("STAR_OFFICE_URL", "http://127.0.0.1:19000").rstrip("/")
AGENT_ID = os.environ.get("STAR_OFFICE_AGENT_ID", "")
VERBOSE = os.environ.get("STAR_OFFICE_VERBOSE", "") == "1"
STATE_DIR = os.path.expanduser(os.environ.get("STAR_OFFICE_BRIDGE_DIR", "~/.claw-office-bridge"))

# Tool name → state mapping
CLAUDE_TOOL_MAP = {
    "Edit": "writing", "Write": "writing", "NotebookEdit": "writing",
    "Bash": "executing", "Read": "researching", "Glob": "researching",
    "Grep": "researching", "Agent": "researching", "WebSearch": "researching",
    "WebFetch": "researching", "TodoWrite": "syncing",
}

CODEX_EVENT_MAP = {
    "turn.started": "writing",
    "item.command_execution.started": "executing",
    "item.command_execution.completed": "executing",
    "item.file_change.started": "writing",
    "item.file_change.completed": "writing",
    "item.reasoning.started": "researching",
    "turn.completed": "idle",
    "turn.failed": "error",
}


def log(msg):
    if VERBOSE:
        print(f"[bridge] {msg}", file=sys.stderr)


def api_request(method, path, data=None):
    """Make HTTP request to office API."""
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        log(f"API error: {e}")
        return None
    except Exception as e:
        log(f"Request error: {e}")
        return None


def get_or_create_agent(name, source):
    """Get existing agent or register new one."""
    state_file = os.path.join(STATE_DIR, f"{source}.json")
    os.makedirs(STATE_DIR, exist_ok=True)

    # Try saved state
    if os.path.exists(state_file):
        with open(state_file, "r") as f:
            state = json.load(f)
            agent_id = state.get("agentId")
            if agent_id:
                # Verify agent still exists
                result = api_request("GET", f"/api/agents/{agent_id}")
                if result and result.get("id"):
                    log(f"Reusing agent {agent_id}")
                    return agent_id

    # Register new agent
    result = api_request("POST", "/api/agents", {
        "name": name,
        "source": source,
        "role": "worker",
    })

    if result and result.get("agent"):
        agent_id = result["agent"]["id"]
        with open(state_file, "w") as f:
            json.dump({"agentId": agent_id, "source": source}, f)
        log(f"Registered agent {agent_id}")
        return agent_id

    log("Failed to register agent")
    return None


def push_state(agent_id, state, detail="", tool_name=None, progress=None,
               token_input=None, token_output=None):
    """Push state update for an agent."""
    data = {"state": state, "detail": detail}
    if tool_name:
        data["toolName"] = tool_name
    if progress is not None:
        data["progress"] = progress
    if token_input is not None:
        data["tokenInput"] = token_input
    if token_output is not None:
        data["tokenOutput"] = token_output

    result = api_request("POST", f"/api/agents/{agent_id}/state", data)
    log(f"Push: {state} - {detail[:50]}")
    return result


def handle_claude_code_hook(agent_id):
    """Handle Claude Code hook event from stdin."""
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        log("Invalid JSON from stdin")
        return

    event_type = event.get("type", "")
    tool_name = event.get("tool", {}).get("name", "") if isinstance(event.get("tool"), dict) else ""

    if event_type == "tool_use":
        state = CLAUDE_TOOL_MAP.get(tool_name, "writing")
        # Extract detail from tool input
        tool_input = event.get("tool", {}).get("input", {})
        if isinstance(tool_input, dict):
            detail = tool_input.get("command", "") or tool_input.get("file_path", "") or tool_input.get("pattern", "") or ""
        else:
            detail = str(tool_input)[:100]
        push_state(agent_id, state, detail=detail[:200], tool_name=tool_name)

    elif event_type == "tool_result":
        pass  # No action needed, we already pushed on tool_use

    elif event_type in ("stop", "end"):
        push_state(agent_id, "idle", detail="Task completed")


def handle_codex_stream(agent_id):
    """Handle Codex CLI JSONL stream from stdin."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type", "")
        state = CODEX_EVENT_MAP.get(event_type)
        if state:
            detail = event.get("content", "") or event.get("command", "") or ""
            push_state(agent_id, state, detail=str(detail)[:200])


def handle_gemini_hook(agent_id):
    """Handle Gemini CLI hook event from stdin."""
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        log("Invalid JSON from stdin")
        return

    action = event.get("action", "")
    tool_name = event.get("tool_name", "")

    if action in ("tool_call", "function_call"):
        if "search" in tool_name.lower() or "read" in tool_name.lower():
            state = "researching"
        elif "write" in tool_name.lower() or "edit" in tool_name.lower():
            state = "writing"
        elif "exec" in tool_name.lower() or "shell" in tool_name.lower():
            state = "executing"
        else:
            state = "writing"
        detail = event.get("arguments", {})
        if isinstance(detail, dict):
            detail = json.dumps(detail)[:100]
        push_state(agent_id, state, detail=str(detail)[:200], tool_name=tool_name)

    elif action in ("complete", "done"):
        push_state(agent_id, "idle", detail="Task completed")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cli_tool = sys.argv[1]

    if cli_tool == "register":
        # Manual registration
        name = "Unknown Agent"
        source = "manual"
        for i, arg in enumerate(sys.argv):
            if arg == "--name" and i + 1 < len(sys.argv):
                name = sys.argv[i + 1]
            if arg == "--source" and i + 1 < len(sys.argv):
                source = sys.argv[i + 1]
        agent_id = get_or_create_agent(name, source)
        if agent_id:
            print(f"Agent registered: {agent_id}")
            print(f"Set: export STAR_OFFICE_AGENT_ID={agent_id}")
        else:
            print("Registration failed", file=sys.stderr)
            sys.exit(1)
        return

    # Determine agent name and source
    source_map = {
        "claude-code": ("Claude Code", "claude-code"),
        "codex": ("Codex CLI", "codex"),
        "gemini": ("Gemini CLI", "gemini"),
        "manual": ("Manual Agent", "manual"),
    }

    if cli_tool not in source_map:
        print(f"Unknown CLI tool: {cli_tool}")
        print(f"Supported: {', '.join(source_map.keys())}")
        sys.exit(1)

    name, source = source_map[cli_tool]

    # Get or create agent
    agent_id = AGENT_ID or get_or_create_agent(name, source)
    if not agent_id:
        sys.exit(1)

    # Handle sub-commands
    if len(sys.argv) >= 3:
        subcmd = sys.argv[2]

        if subcmd == "hook":
            if cli_tool == "claude-code":
                handle_claude_code_hook(agent_id)
            elif cli_tool == "gemini":
                handle_gemini_hook(agent_id)
            else:
                print(f"Hook mode not supported for {cli_tool}")

        elif subcmd == "--stream":
            handle_codex_stream(agent_id)

        elif subcmd in ("idle", "writing", "researching", "executing", "syncing", "error", "reviewing"):
            # Manual state push
            detail = sys.argv[3] if len(sys.argv) > 3 else ""
            push_state(agent_id, subcmd, detail=detail)

        else:
            print(f"Unknown sub-command: {subcmd}")
            sys.exit(1)
    else:
        print(f"Agent ID: {agent_id}")
        print(f"Use: python3 {sys.argv[0]} {cli_tool} hook|--stream|<state> [detail]")


if __name__ == "__main__":
    main()
