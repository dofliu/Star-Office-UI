#!/usr/bin/env python3
"""
AI Office Bridge — 將 AI CLI 工具的狀態即時推送到 Star Office UI

支援三種 AI CLI：
  1. Claude Code  — 透過 hooks 系統呼叫（PreToolUse / Stop 等事件）
  2. Gemini CLI   — 透過 hooks 系統呼叫（BeforeTool / AfterAgent 等事件）
  3. Codex CLI    — 透過 `codex exec --json` 的 JSONL 串流管道

用法：
  # Claude Code / Gemini CLI hooks（事件模式）
  python3 ai-office-bridge.py <cli-name> <state> [detail]

  # Codex CLI JSONL 串流模式
  codex exec --json "task" 2>&1 | python3 ai-office-bridge.py codex --stream

  # 離開辦公室
  python3 ai-office-bridge.py <cli-name> --leave

環境變數：
  STAR_OFFICE_URL      辦公室伺服器位址（預設 http://127.0.0.1:19000）
  STAR_OFFICE_JOIN_KEY  加入金鑰（必填，格式 ocj_*）
  STAR_OFFICE_BRIDGE_DIR  橋接狀態檔存放目錄（預設 ~/.star-office-bridge/）
  STAR_OFFICE_VERBOSE   除錯輸出（設 1 啟用）
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ── 設定 ──────────────────────────────────────────────────

OFFICE_URL = os.environ.get("STAR_OFFICE_URL", "http://127.0.0.1:19000").rstrip("/")
JOIN_KEY = os.environ.get("STAR_OFFICE_JOIN_KEY", "")
BRIDGE_DIR = Path(os.environ.get("STAR_OFFICE_BRIDGE_DIR", os.path.expanduser("~/.star-office-bridge")))
VERBOSE = os.environ.get("STAR_OFFICE_VERBOSE", "0") in {"1", "true", "yes"}

JOIN_ENDPOINT = "/join-agent"
PUSH_ENDPOINT = "/agent-push"
LEAVE_ENDPOINT = "/leave-agent"

# CLI 名稱到辦公室顯示名稱的對應
CLI_DISPLAY_NAMES = {
    "claude-code": "Claude Code",
    "claude":      "Claude Code",
    "codex":       "Codex CLI",
    "gemini":      "Gemini CLI",
}

# ── 工具名稱到狀態的映射 ─────────────────────────────────

# Claude Code 工具名稱
CLAUDE_TOOL_STATE_MAP = {
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
}

# Gemini CLI 工具名稱（常見）
GEMINI_TOOL_STATE_MAP = {
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
        print(f"[bridge] {msg}", file=sys.stderr)


# ── 狀態檔管理 ────────────────────────────────────────────

def _state_path(cli_name):
    """每個 CLI 獨立一個狀態檔。"""
    safe = cli_name.replace("/", "_").replace(" ", "_")
    return BRIDGE_DIR / f"{safe}.json"


def load_agent_state(cli_name):
    fp = _state_path(cli_name)
    if fp.exists():
        try:
            return json.loads(fp.read_text("utf-8"))
        except Exception:
            pass
    return {"agentId": None, "joined": False, "joinKey": JOIN_KEY, "cli": cli_name}


def save_agent_state(cli_name, data):
    BRIDGE_DIR.mkdir(parents=True, exist_ok=True)
    _state_path(cli_name).write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")


# ── HTTP 呼叫 ─────────────────────────────────────────────

def _post(path, payload, timeout=5):
    """輕量 HTTP POST，優先用 urllib 避免外部依賴。"""
    import urllib.request
    import urllib.error

    url = f"{OFFICE_URL}{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
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


# ── 加入 / 推送 / 離開 ───────────────────────────────────

def ensure_joined(cli_name):
    """確保已加入辦公室，回傳 agent 狀態 dict。"""
    state = load_agent_state(cli_name)

    if state.get("joined") and state.get("agentId"):
        return state

    if not JOIN_KEY:
        print("Error: STAR_OFFICE_JOIN_KEY not set", file=sys.stderr)
        sys.exit(1)

    display_name = CLI_DISPLAY_NAMES.get(cli_name, cli_name)
    payload = {
        "name": display_name,
        "joinKey": JOIN_KEY,
        "state": "idle",
        "detail": "AI CLI 已連線",
    }

    code, body = _post(JOIN_ENDPOINT, payload)
    if code in (200, 201) and body.get("ok"):
        state["joined"] = True
        state["agentId"] = body["agentId"]
        state["joinKey"] = JOIN_KEY
        save_agent_state(cli_name, state)
        _log(f"Joined as {display_name}, agentId={state['agentId']}")
        return state

    print(f"Error: join failed ({code}): {body}", file=sys.stderr)
    sys.exit(1)


def push_state(cli_name, office_state, detail=""):
    """推送狀態到辦公室。"""
    agent = ensure_joined(cli_name)
    display_name = CLI_DISPLAY_NAMES.get(cli_name, cli_name)

    payload = {
        "agentId": agent["agentId"],
        "joinKey": agent.get("joinKey", JOIN_KEY),
        "state": office_state,
        "detail": detail[:200] if detail else "",
        "name": display_name,
    }

    code, body = _post(PUSH_ENDPOINT, payload)
    if code in (200, 201) and body.get("ok"):
        area = body.get("area", "?")
        _log(f"Pushed: state={office_state} area={area} detail={detail[:60]}")
        return True

    if code in (403, 404):
        _log(f"Push rejected ({code}), re-joining...")
        agent["joined"] = False
        agent["agentId"] = None
        save_agent_state(cli_name, agent)
        # 重新 join 然後再推一次
        agent = ensure_joined(cli_name)
        payload["agentId"] = agent["agentId"]
        payload["joinKey"] = agent.get("joinKey", JOIN_KEY)
        code2, body2 = _post(PUSH_ENDPOINT, payload)
        if code2 in (200, 201) and body2.get("ok"):
            _log(f"Re-push succeeded after rejoin")
            return True

    _log(f"Push failed ({code}): {body}")
    return False


def leave(cli_name):
    """離開辦公室。"""
    agent = load_agent_state(cli_name)
    if not agent.get("agentId"):
        _log("Not joined, nothing to leave")
        return

    payload = {"agentId": agent["agentId"]}
    code, body = _post(LEAVE_ENDPOINT, payload)
    _log(f"Leave: {code} {body}")

    agent["joined"] = False
    agent["agentId"] = None
    save_agent_state(cli_name, agent)


# ── Claude Code hook 模式 ────────────────────────────────

def handle_claude_hook():
    """從 stdin 讀取 Claude Code hook JSON，推斷狀態。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None, None
        event = json.loads(raw)
    except Exception:
        return None, None

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # 從工具名推斷狀態
    state = CLAUDE_TOOL_STATE_MAP.get(tool_name, "writing")

    # 嘗試生成有意義的 detail
    detail = ""
    if tool_name == "Bash":
        cmd = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
        detail = f"$ {cmd[:80]}" if cmd else "Executing command"
    elif tool_name in ("Edit", "Write"):
        fp = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""
        detail = f"Editing {os.path.basename(fp)}" if fp else "Editing file"
    elif tool_name in ("Read", "Glob", "Grep"):
        detail = f"Reading codebase"
    elif tool_name == "Agent":
        detail = tool_input.get("description", "Sub-agent") if isinstance(tool_input, dict) else "Sub-agent"
    elif tool_name in ("WebSearch", "WebFetch"):
        detail = "Web research"
    else:
        detail = f"Tool: {tool_name}" if tool_name else ""

    return state, detail


# ── Gemini CLI hook 模式 ─────────────────────────────────

def handle_gemini_hook():
    """從 stdin 讀取 Gemini CLI hook JSON，推斷狀態。"""
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return None, None
        event = json.loads(raw)
    except Exception:
        return None, None

    tool_name = event.get("tool_name", "") or event.get("function_name", "")
    state = GEMINI_TOOL_STATE_MAP.get(tool_name, "writing")
    detail = f"Tool: {tool_name}" if tool_name else "Working"

    return state, detail


# ── Codex CLI JSONL 串流模式 ─────────────────────────────

def handle_codex_stream():
    """從 stdin 持續讀取 Codex CLI JSONL 事件，推送狀態。"""
    cli_name = "codex"
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
        state = None
        detail = ""

        if event_type == "turn.started":
            state = "writing"
            detail = "Processing task"
        elif event_type in ("item.command_execution.started", "item.command_execution.running"):
            state = "executing"
            cmd = event.get("command", "") or ""
            detail = f"$ {cmd[:80]}" if cmd else "Executing"
        elif event_type == "item.file_change.started":
            state = "writing"
            fp = event.get("file", "") or ""
            detail = f"Editing {os.path.basename(fp)}" if fp else "Editing file"
        elif event_type == "item.message.started":
            state = "writing"
            detail = "Composing response"
        elif event_type == "item.reasoning.started":
            state = "researching"
            detail = "Thinking..."
        elif event_type in ("turn.completed", "turn.failed"):
            state = "idle"
            detail = "Task completed" if "completed" in event_type else "Task failed"
        elif event_type == "item.web_search.started":
            state = "researching"
            detail = "Web search"

        if state and state != last_state:
            push_state(cli_name, state, detail)
            last_state = state

    # 串流結束，回 idle
    if last_state != "idle":
        push_state(cli_name, "idle", "Stream ended")


# ── 主程式 ────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    cli_name = sys.argv[1].lower()

    # --leave 模式
    if len(sys.argv) >= 3 and sys.argv[2] == "--leave":
        leave(cli_name)
        print(f"Left office as {cli_name}", file=sys.stderr)
        sys.exit(0)

    # --stream 模式（Codex）
    if len(sys.argv) >= 3 and sys.argv[2] == "--stream":
        _log("Starting Codex JSONL stream mode")
        handle_codex_stream()
        sys.exit(0)

    # 事件模式：ai-office-bridge.py <cli> <state> [detail]
    if len(sys.argv) >= 3 and sys.argv[2] not in ("--stream", "--leave"):
        state = sys.argv[2]
        detail = sys.argv[3] if len(sys.argv) >= 4 else ""

        # 特殊處理：如果 state 是 "hook"，從 stdin 讀取 hook 資料
        if state == "hook":
            if cli_name in ("claude-code", "claude"):
                state, detail = handle_claude_hook()
            elif cli_name == "gemini":
                state, detail = handle_gemini_hook()

            if not state:
                sys.exit(0)  # 無法判斷，靜默退出

        push_state(cli_name, state, detail)
        sys.exit(0)

    # 無參數模式：嘗試從 stdin 讀取 hook 資料
    if cli_name in ("claude-code", "claude"):
        state, detail = handle_claude_hook()
    elif cli_name == "gemini":
        state, detail = handle_gemini_hook()
    else:
        print(f"Unknown mode for {cli_name}. Use --stream for codex.", file=sys.stderr)
        sys.exit(1)

    if state:
        push_state(cli_name, state, detail)


if __name__ == "__main__":
    main()
