#!/bin/bash
# Star Office UI V2 - One-click AI Hook Setup
#
# 自動設定 Claude Code / Gemini CLI 的 hooks，
# 讓 AI 工具的工作狀態即時顯示在 Star Office UI 儀表板。
#
# 用法：
#   bash scripts/setup-hooks.sh
#   bash scripts/setup-hooks.sh --url http://your-server:19200
#
# 做了什麼：
#   1. 偵測已安裝的 AI CLI 工具
#   2. 設定各工具的 hooks（自動推送狀態）
#   3. 註冊預設 agent
#   4. 顯示驗證指令

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BRIDGE_SCRIPT="$SCRIPT_DIR/ai-office-bridge-v2.py"

# 解析參數
OFFICE_URL="${STAR_OFFICE_URL:-http://127.0.0.1:19200}"
if [ "$1" = "--url" ] && [ -n "$2" ]; then
    OFFICE_URL="$2"
elif [ -n "$1" ] && [ "$1" != "--url" ]; then
    OFFICE_URL="$1"
fi

echo "╔══════════════════════════════════════════╗"
echo "║   ⭐ Star Office UI — Hook Setup        ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Server URL:    $OFFICE_URL"
echo "  Bridge Script: $BRIDGE_SCRIPT"
echo ""

# 檢查橋接腳本
if [ ! -f "$BRIDGE_SCRIPT" ]; then
    echo "ERROR: Bridge script not found at $BRIDGE_SCRIPT"
    exit 1
fi

# --- Claude Code ---
setup_claude_code() {
    echo "── Claude Code ──────────────────────────"

    if ! command -v claude &> /dev/null; then
        echo "  ⚠ Claude Code CLI not found, skipping."
        echo "  (Install: npm install -g @anthropic-ai/claude-code)"
        return
    fi

    echo "  ✓ Claude Code detected"

    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    mkdir -p "$HOME/.claude"

    HOOK_CMD="STAR_OFFICE_URL=$OFFICE_URL python3 $BRIDGE_SCRIPT --hook claude-code"

    if [ -f "$CLAUDE_SETTINGS" ]; then
        cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.bak"
        echo "  Backed up settings → $CLAUDE_SETTINGS.bak"
    fi

    python3 -c "
import json, os

settings_file = '$CLAUDE_SETTINGS'
hook_cmd = '$HOOK_CMD'

settings = {}
if os.path.exists(settings_file):
    with open(settings_file) as f:
        settings = json.load(f)

if 'hooks' not in settings:
    settings['hooks'] = {}

# PreToolUse hook — 在每次工具呼叫前推送狀態
settings['hooks']['PreToolUse'] = [{
    'type': 'command',
    'command': hook_cmd
}]

# Stop hook — AI 完成任務後回 idle
settings['hooks']['Stop'] = [{
    'type': 'command',
    'command': 'echo {\"type\":\"Stop\"} | ' + hook_cmd
}]

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print('  ✓ Claude Code hooks configured')
print(f'    → {settings_file}')
"
}

# --- Gemini CLI ---
setup_gemini() {
    echo ""
    echo "── Gemini CLI ───────────────────────────"

    if ! command -v gemini &> /dev/null; then
        echo "  ⚠ Gemini CLI not found, skipping."
        return
    fi

    echo "  ✓ Gemini CLI detected"

    GEMINI_SETTINGS="$HOME/.gemini/settings.json"
    mkdir -p "$HOME/.gemini"

    HOOK_CMD="STAR_OFFICE_URL=$OFFICE_URL python3 $BRIDGE_SCRIPT --hook gemini"

    python3 -c "
import json, os

settings_file = '$GEMINI_SETTINGS'
hook_cmd = '$HOOK_CMD'

settings = {}
if os.path.exists(settings_file):
    with open(settings_file) as f:
        settings = json.load(f)

if 'hooks' not in settings:
    settings['hooks'] = {}

settings['hooks']['post_tool_use'] = [{
    'type': 'command',
    'command': hook_cmd
}]

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print('  ✓ Gemini CLI hooks configured')
print(f'    → {settings_file}')
"
}

# --- 註冊預設 Agent ---
register_agents() {
    echo ""
    echo "── Registering Agents ─────────────────"
    export STAR_OFFICE_URL="$OFFICE_URL"

    # 嘗試註冊預設 agent
    python3 "$BRIDGE_SCRIPT" --register claude "Claude Code" char_purple 2>/dev/null && \
        echo "  ✓ Claude Code agent registered" || \
        echo "  ⚠ Could not register (server may not be running)"
}

# --- 執行 ---
setup_claude_code
setup_gemini
register_agents

echo ""
echo "══════════════════════════════════════════"
echo ""
echo "  ✓ Setup complete!"
echo ""
echo "  Dashboard:  $OFFICE_URL"
echo "  Server:     python3 $PROJECT_DIR/server/app.py"
echo ""
echo "  Manual test commands:"
echo "    python3 $BRIDGE_SCRIPT --status"
echo "    python3 $BRIDGE_SCRIPT claude writing '正在寫程式'"
echo "    python3 $BRIDGE_SCRIPT claude idle"
echo ""
echo "  Add to your shell config (.bashrc / .zshrc):"
echo "    export STAR_OFFICE_URL=$OFFICE_URL"
echo ""
