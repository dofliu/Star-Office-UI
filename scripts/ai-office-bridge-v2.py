#!/usr/bin/env python3
"""
AI Office Bridge V2 — 將 AI CLI 工具的狀態即時推送到 Star Office UI V2 API

支援：
  1. Claude Code  — 透過 hooks 系統自動推送（PreToolUse / PostToolUse / Stop）
  2. Gemini CLI   — 透過 hooks 系統自動推送
  3. Codex CLI    — JSONL 串流模式
  4. 手動推送     — 直接設定 agent 狀態

用法：
  # 手動推送狀態
  python3 ai-office-bridge-v2.py <agent-id> <state> [message]
  python3 ai-office-bridge-v2.py claude writing "正在編輯程式碼"
  python3 ai-office-bridge-v2.py claude idle

  # Claude Code hooks 模式（從 stdin 讀取 hook JSON）
  python3 ai-office-bridge-v2.py --hook claude-code < hook-event.json

  # Codex CLI JSONL 串流模式
  codex exec --json "task" 2>&1 | python3 ai-office-bridge-v2.py --hook codex --stream

  # 註冊新 agent（首次使用）
  python3 ai-office-bridge-v2.py --register <agent-id> <display-name> [avatar]
  python3 ai-office-bridge-v2.py --register claude "Claude Code" char_purple

  # 移除 agent
  python3 ai-office-bridge-v2.py --remove <agent-id>

  # 查看所有 agent 狀態
  python3 ai-office-bridge-v2.py --status

環境變數：
  STAR_OFFICE_URL      V2 伺服器位址（預設 http://127.0.0.1:19200）
  STAR_OFFICE_VERBOSE  除錯輸出（設 1 啟用）
"""

import json
import os
import sys
import urllib.request
import urllib.error

# ── 設定 ──────────────────────────────────────────────────

OFFICE_URL = os.environ.get("STAR_OFFICE_URL", "http://127.0.0.1:19200").rstrip("/")
VERBOSE = os.environ.get("STAR_OFFICE_VERBOSE", "0") in {"1", "true", "yes"}

# CLI 名稱到預設 agent 設定
CLI_DEFAULTS = {
    "claude-code": {"id": "claude", "name": "Claude Code", "avatar": "char_purple"},
    "claude":      {"id": "claude", "name": "Claude Code", "avatar": "char_purple"},
    "gemini":      {"id": "gemini", "name": "Gemini CLI", "avatar": "char_green"},
    "codex":       {"id": "codex",  "name": "Codex CLI",  "avatar": "char_orange"},
}

# Claude Code 工具名稱 → 狀態映射
CLAUDE_TOOL_MAP = {
    "Edit":         "writing",
    "Write":        "writing",
    "NotebookEdit": "writing",
    "Bash":         "executing",
    "Read":         "researching",
    "Glob":         "researching",
    "Grep":         "researching",
    "Agent":        "researching",
    "WebSearch":    "researching",
    "WebFetch":     "researching",
    "TodoWrite":    "writing",
}

# Codex CLI 事件 → 狀態映射
CODEX_EVENT_MAP = {
    "turn.started":                      "writing",
    "item.command_execution.started":    "executing",
    "item.command_execution.running":    "executing",
    "item.file_change.started":          "writing",
    "item.message.started":              "writing",
    "item.reasoning.started":            "researching",
    "item.web_search.started":           "researching",
    "turn.completed":                    "idle",
    "turn.failed":                       "error",
}

# Gemini CLI 工具名稱 → 狀態映射
GEMINI_TOOL_MAP = {
    "edit_file":     "writing",
    "write_file":    "writing",
    "run_command":   "executing",
    "shell":         "executing",
    "read_file":     "researching",
    "search_files":  "researching",
    "web_search":    "researching",
    "google_search": "researching",
}


def _log(msg):
    if VERBOSE:
        print(f"[bridge-v2] {msg}", file=sys.stderr)


# ── HTTP 工具 ─────────────────────────────────────────────

def _request(method, path, payload=None, timeout=5):
    """輕量 HTTP 請求（urllib，無需外部依賴）。"""
    url = f"{OFFICE_URL}{path}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = {}
        try:
            body = json.loads(e.read().decode("utf-8"))
        except Exception:
            pass
        return e.code, body
    except Exception as e:
        _log(f"HTTP error: {e}")
        return 0, {"error": str(e)}


# ── 核心操作（V2 API: /agents, /agents/<id>/state）────────

def ensure_agent(agent_id, name="", avatar=""):
    """確保 agent 已註冊，若不存在則自動建立。"""
    code, body = _request("GET", f"/agents/{agent_id}")
    if code == 200:
        _log(f"Agent '{agent_id}' exists")
        return True

    # 自動註冊
    if not name:
        defaults = CLI_DEFAULTS.get(agent_id, {})
        name = defaults.get("name", agent_id)
        avatar = avatar or defaults.get("avatar", "char_blue")

    payload = {"id": agent_id, "name": name}
    if avatar:
        payload["avatar"] = avatar

    code, body = _request("POST", "/agents", payload)
    if code == 201:
        _log(f"Auto-registered agent '{agent_id}' as '{name}'")
        return True
    elif code == 409:
        _log(f"Agent '{agent_id}' already exists")
        return True

    print(f"Error: failed to register agent ({code}): {body}", file=sys.stderr)
    return False


def push_state(agent_id, state, message="", progress=0):
    """推送狀態到 V2 API: POST /agents/<id>/state。"""
    if not ensure_agent(agent_id):
        return False

    payload = {"state": state}
    if message:
        payload["message"] = message[:200]
    if progress:
        payload["progress"] = progress

    code, body = _request("POST", f"/agents/{agent_id}/state", payload)
    if code == 200:
        _log(f"OK: {agent_id} → {state} ({message[:60]})")
        return True

    print(f"Error: push failed ({code}): {body}", file=sys.stderr)
    return False


def register_agent(agent_id, name, avatar=""):
    """明確註冊新 agent: POST /agents。"""
    payload = {"id": agent_id, "name": name}
    if avatar:
        payload["avatar"] = avatar
    code, body = _request("POST", "/agents", payload)
    if code == 201:
        print(f"OK: Registered '{agent_id}' ({name})")
        return True
    elif code == 409:
        print(f"Agent '{agent_id}' already exists")
        return True
    print(f"Error ({code}): {body}")
    return False


def remove_agent(agent_id):
    """移除 agent: DELETE /agents/<id>。"""
    code, body = _request("DELETE", f"/agents/{agent_id}")
    if code == 200:
        print(f"OK: Removed '{agent_id}'")
        return True
    print(f"Error ({code}): {body}")
    return False


def show_status():
    """顯示所有 agent 狀態: GET /api/status。"""
    code, body = _request("GET", "/api/status")
    if code != 200:
        print(f"Error ({code}): cannot reach {OFFICE_URL}", file=sys.stderr)
        return

    print(f"⭐ Star Office — {body.get('agent_count', 0)} agent(s) — {OFFICE_URL}")
    print("-" * 55)
    for a in body.get("agents", []):
        label = a.get("label", a.get("name", a["id"]))
        state = a.get("state", "?")
        msg = a.get("message", "")
        msg_str = f"  {msg}" if msg else ""
        print(f"  [{state:^12}] {label} (#{a['id']}){msg_str}")
    if not body.get("agents"):
        print("  (no agents registered)")


# ── Claude Code Hook 處理 ────────────────────────────────

def handle_claude_hook(agent_id):
    """從 stdin 讀取 Claude Code hook JSON，推斷狀態並推送。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        event = json.loads(raw)
    except Exception:
        return

    hook_type = event.get("type", "")
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    if isinstance(tool_input, str):
        tool_input = {}

    # Stop / Notification → idle
    if hook_type in ("Stop", "Notification"):
        push_state(agent_id, "idle", "任務完成")
        return

    # PreToolUse / PostToolUse → 推斷工作狀態
    state = CLAUDE_TOOL_MAP.get(tool_name, "writing")

    # 生成有意義的描述
    message = ""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        message = f"$ {cmd[:80]}" if cmd else "Executing command"
    elif tool_name in ("Edit", "Write"):
        fp = tool_input.get("file_path", "")
        message = f"Editing {os.path.basename(fp)}" if fp else "Editing file"
    elif tool_name in ("Read", "Glob", "Grep"):
        message = "Reading codebase"
    elif tool_name == "Agent":
        message = tool_input.get("description", "Sub-agent research")
    elif tool_name in ("WebSearch", "WebFetch"):
        message = "Web research"
    elif tool_name:
        message = f"Tool: {tool_name}"

    push_state(agent_id, state, message)


def handle_gemini_hook(agent_id):
    """從 stdin 讀取 Gemini CLI hook JSON。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return
        event = json.loads(raw)
    except Exception:
        return

    tool_name = event.get("tool_name", "") or event.get("function_name", "")
    state = GEMINI_TOOL_MAP.get(tool_name, "writing")
    message = f"Tool: {tool_name}" if tool_name else "Working"
    push_state(agent_id, state, message)


def handle_codex_stream(agent_id):
    """從 stdin 持續讀取 Codex CLI JSONL 事件。"""
    last_state = None
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except Exception:
            continue

        event_type = event.get("type", "")
        state = CODEX_EVENT_MAP.get(event_type)
        if state and state != last_state:
            detail = event.get("command", "") or event.get("content", "") or ""
            push_state(agent_id, state, str(detail)[:200])
            last_state = state

    if last_state != "idle":
        push_state(agent_id, "idle", "Stream ended")


# ── 主程式 ────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg1 = sys.argv[1]

    # --status: 查看狀態
    if arg1 == "--status":
        show_status()
        return

    # --register <id> <name> [avatar]
    if arg1 == "--register":
        if len(sys.argv) < 4:
            print("Usage: --register <agent-id> <display-name> [avatar]")
            sys.exit(1)
        avatar = sys.argv[4] if len(sys.argv) >= 5 else ""
        register_agent(sys.argv[2], sys.argv[3], avatar)
        return

    # --remove <id>
    if arg1 == "--remove":
        if len(sys.argv) < 3:
            print("Usage: --remove <agent-id>")
            sys.exit(1)
        remove_agent(sys.argv[2])
        return

    # --hook <cli-name> [--stream]
    if arg1 == "--hook":
        cli_name = sys.argv[2] if len(sys.argv) >= 3 else "claude-code"
        defaults = CLI_DEFAULTS.get(cli_name, {})
        agent_id = defaults.get("id", cli_name)

        # --stream for codex
        if len(sys.argv) >= 4 and sys.argv[3] == "--stream":
            handle_codex_stream(agent_id)
            return

        if cli_name in ("claude-code", "claude"):
            handle_claude_hook(agent_id)
        elif cli_name == "gemini":
            handle_gemini_hook(agent_id)
        elif cli_name == "codex":
            handle_codex_stream(agent_id)
        else:
            print(f"Unknown CLI: {cli_name}", file=sys.stderr)
            sys.exit(1)
        return

    # <agent-id> <state> [message]
    agent_id = arg1
    if len(sys.argv) < 3:
        # 只給 agent-id，顯示該 agent 狀態
        code, body = _request("GET", f"/agents/{agent_id}")
        if code == 200:
            print(json.dumps(body, ensure_ascii=False, indent=2))
        else:
            print(f"Agent '{agent_id}' not found")
        return

    state = sys.argv[2]
    message = " ".join(sys.argv[3:]) if len(sys.argv) >= 4 else ""
    push_state(agent_id, state, message)


if __name__ == "__main__":
    main()
