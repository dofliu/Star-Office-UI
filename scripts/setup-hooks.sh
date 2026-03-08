#!/bin/bash
# Claw Office UI - One-click AI Hook Setup
#
# This script configures Claude Code, Codex CLI, and Gemini CLI
# to automatically push status to the Claw Office UI dashboard.
#
# Usage:
#   bash scripts/setup-hooks.sh [--url http://host:port]
#
# What it does:
#   1. Detects which AI CLI tools are installed
#   2. Configures hooks/settings for each tool
#   3. Registers agents with the office server
#   4. Shows verification commands

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BRIDGE_SCRIPT="$SCRIPT_DIR/ai-office-bridge-v2.py"
OFFICE_URL="${1:-${STAR_OFFICE_URL:-http://127.0.0.1:19000}}"

# Remove --url flag if present
if [ "$1" = "--url" ]; then
    OFFICE_URL="${2:-http://127.0.0.1:19000}"
fi

echo "=== Claw Office UI - Hook Setup ==="
echo "Office URL: $OFFICE_URL"
echo "Bridge Script: $BRIDGE_SCRIPT"
echo ""

# Check bridge script exists
if [ ! -f "$BRIDGE_SCRIPT" ]; then
    echo "ERROR: Bridge script not found at $BRIDGE_SCRIPT"
    exit 1
fi

# --- Claude Code ---
setup_claude_code() {
    echo "--- Setting up Claude Code ---"

    CLAUDE_SETTINGS="$HOME/.claude/settings.json"
    mkdir -p "$HOME/.claude"

    # Check if Claude Code is installed
    if ! command -v claude &> /dev/null; then
        echo "  Claude Code CLI not found, skipping."
        return
    fi

    # Create or update settings with hooks
    HOOK_CMD="STAR_OFFICE_URL=$OFFICE_URL python3 $BRIDGE_SCRIPT claude-code hook"

    if [ -f "$CLAUDE_SETTINGS" ]; then
        # Backup
        cp "$CLAUDE_SETTINGS" "$CLAUDE_SETTINGS.bak"
        echo "  Backed up existing settings to $CLAUDE_SETTINGS.bak"
    fi

    # Use Python to safely merge JSON
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

settings['hooks']['PostToolUse'] = [{
    'type': 'command',
    'command': hook_cmd
}]

with open(settings_file, 'w') as f:
    json.dump(settings, f, indent=2)

print('  Claude Code hooks configured successfully.')
"
}

# --- Codex CLI ---
setup_codex() {
    echo "--- Setting up Codex CLI ---"

    if ! command -v codex &> /dev/null; then
        echo "  Codex CLI not found, skipping."
        return
    fi

    echo "  Codex CLI detected."
    echo "  To use with Claw Office, pipe output through bridge:"
    echo ""
    echo "    export STAR_OFFICE_URL=$OFFICE_URL"
    echo "    codex exec --json 'your task' 2>&1 | python3 $BRIDGE_SCRIPT codex --stream"
    echo ""
    echo "  Or add this alias to your shell config:"
    echo "    alias codex-office='codex exec --json 2>&1 | STAR_OFFICE_URL=$OFFICE_URL python3 $BRIDGE_SCRIPT codex --stream'"
}

# --- Gemini CLI ---
setup_gemini() {
    echo "--- Setting up Gemini CLI ---"

    if ! command -v gemini &> /dev/null; then
        echo "  Gemini CLI not found, skipping."
        return
    fi

    echo "  Gemini CLI detected."
    GEMINI_SETTINGS="$HOME/.gemini/settings.json"
    mkdir -p "$HOME/.gemini"

    HOOK_CMD="STAR_OFFICE_URL=$OFFICE_URL python3 $BRIDGE_SCRIPT gemini hook"

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

print('  Gemini CLI hooks configured successfully.')
"
}

# --- Register Agents ---
register_agents() {
    echo ""
    echo "--- Registering Agents ---"
    export STAR_OFFICE_URL="$OFFICE_URL"

    # Try to register default agents
    for tool in claude-code codex gemini; do
        python3 "$BRIDGE_SCRIPT" "$tool" idle "Setup complete" 2>/dev/null || true
    done
    echo "  Agent registration complete."
}

# Run setup
setup_claude_code
echo ""
setup_codex
echo ""
setup_gemini
register_agents

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Dashboard: $OFFICE_URL"
echo ""
echo "To start the office server:"
echo "  cd $(dirname $SCRIPT_DIR) && python3 backend/app_v2.py"
echo ""
echo "Environment variables (add to your .bashrc/.zshrc):"
echo "  export STAR_OFFICE_URL=$OFFICE_URL"
