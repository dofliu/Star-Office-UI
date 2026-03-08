# AI CLI Hooks 設定指南 — Star Office UI

讓 AI CLI 工具的工作狀態即時顯示在 Star Office UI 辦公室中。

## 前置需求

1. Star Office UI 後端正在執行（預設 `http://127.0.0.1:19000`）
2. 一把有效的 join key（在 `join-keys.json` 中設定，格式 `ocj_*`）
3. Python 3.10+（橋接腳本使用，無外部依賴）

## 環境變數設定

```bash
# 必填
export STAR_OFFICE_JOIN_KEY="ocj_example_team_01"

# 選填（有預設值）
export STAR_OFFICE_URL="http://127.0.0.1:19000"
export STAR_OFFICE_BRIDGE_DIR="$HOME/.star-office-bridge"
export STAR_OFFICE_VERBOSE=1  # 除錯模式
```

建議加入 `~/.bashrc` 或 `~/.zshrc`。

---

## 1. Claude Code

Claude Code 有 14 種 hooks 事件。我們使用 `PreToolUse`（偵測工作中）和 `Stop`（偵測完成）。

### 設定 `~/.claude/settings.json`

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py claude-code hook"
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py claude-code idle 'Task completed'"
          }
        ]
      }
    ]
  }
}
```

> **注意：** 將 `/path/to/` 替換為實際路徑。`PreToolUse` hook 會從 stdin 接收工具名稱 JSON，自動推斷狀態。

### Claude Code hook 事件對應

| Hook 事件 | 辦公室狀態 | 說明 |
|-----------|-----------|------|
| `PreToolUse` (Edit/Write) | `writing` | 正在編輯程式碼 |
| `PreToolUse` (Bash) | `executing` | 執行指令 |
| `PreToolUse` (Read/Grep/Glob) | `researching` | 閱讀/搜尋程式碼 |
| `PreToolUse` (Agent) | `researching` | 子代理人工作中 |
| `Stop` | `idle` | 任務完成 |

---

## 2. Gemini CLI

Gemini CLI（v0.26.0+）支援 hooks。注意 hooks 是同步執行，腳本須盡快完成。

### 設定 `~/.gemini/settings.json`

```jsonc
{
  "hooks": {
    "BeforeTool": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py gemini hook"
          }
        ]
      }
    ],
    "AfterAgent": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py gemini idle 'Task completed'"
          }
        ]
      }
    ]
  }
}
```

---

## 3. Codex CLI (OpenAI)

Codex CLI 沒有 hooks 系統，但 `codex exec --json` 會輸出 JSONL 事件串流。

### 用法

```bash
# 用管道將 JSONL 串流送入橋接腳本
codex exec --json "implement feature X" 2>&1 | \
  python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py codex --stream
```

### Codex JSONL 事件對應

| JSONL event type | 辦公室狀態 | 說明 |
|------------------|-----------|------|
| `turn.started` | `writing` | 開始處理 |
| `item.command_execution.*` | `executing` | 執行指令 |
| `item.file_change.*` | `writing` | 編輯檔案 |
| `item.reasoning.*` | `researching` | 推理中 |
| `item.web_search.*` | `researching` | 網路搜尋 |
| `turn.completed` | `idle` | 完成 |
| `turn.failed` | `idle` | 失敗 |

### 建立便捷 alias

```bash
alias codex-office='function _co() {
  codex exec --json "$@" 2>&1 | \
    python3 /path/to/Star-Office-UI/scripts/ai-office-bridge.py codex --stream
}; _co'
```

---

## 手動測試

```bash
# 測試推送 writing 狀態
python3 scripts/ai-office-bridge.py claude-code writing "Testing bridge"

# 測試推送 idle
python3 scripts/ai-office-bridge.py claude-code idle

# 離開辦公室
python3 scripts/ai-office-bridge.py claude-code --leave
```

---

## 辦公室效果

設定完成後，你會在 Star Office UI 中看到：

```
┌─────────────────────────────────────────────┐
│  ☕ 休息區                    🖥️ 伺服器區    │
│   ⭐ Gemini CLI (idle)        🐛 Bug 角落   │
│                                              │
│  📝 工作區                                   │
│   ⭐ Star (writing)                          │
│   ⭐ Claude Code (writing "Edit app.py")     │
│   ⭐ Codex CLI (executing "npm test")        │
│                                              │
└─────────────────────────────────────────────┘
```

每個 AI CLI 在辦公室裡是獨立的角色，各自有自己的狀態。

---

## 疑難排解

| 問題 | 解決方式 |
|------|---------|
| `STAR_OFFICE_JOIN_KEY not set` | 設定環境變數 `STAR_OFFICE_JOIN_KEY` |
| Join 失敗 403 | 檢查 `join-keys.json` 中的 key 是否有效 |
| 狀態沒更新 | 開啟 `STAR_OFFICE_VERBOSE=1` 查看 stderr 輸出 |
| Gemini hook 導致延遲 | 確認腳本快速完成（<1s），避免阻塞 |
| 角色顯示 offline | 確認持續推送中（Codex 串流或持續觸發 hooks）|
