# CLAUDE.md — Star Office UI

> 最後更新：2026-03-08 (Phase 6 completed)
> 本文件是給 AI 開發者（Claude Code、Gemini CLI 等）的完整專案說明，確保跨 session 能無縫接續開發。

---

## 專案概述

Star Office UI 是一個**像素風格的 AI 辦公室儀表板**，在瀏覽器中以 2D 像素遊戲畫面即時呈現 AI 助理/代理人的工作狀態。

**核心價值**：讓老闆（劉瑞弘 dof）能隨時看到所有 AI 助手在做什麼。

**開發者**：春野櫻 🌸（主要 AI）+ Claude Code K（助手 AI）

---

## 雙軌架構（重要！）

本專案目前有**兩套系統並行**，開發時請注意區分：

### V1（舊版）— Port 19000
- `backend/app.py` — 單體 Flask 應用（~2,000 LOC）
- `frontend/` — 完整 Phaser 3 + sprite 素材
- 功能完整但程式碼龐大，不易維護

### V2（新版，主力開發中）— Port 19200
- `core/` — 純 Python 核心引擎（agent 狀態機 + office 管理）
- `server/app.py` — 輕量 Flask REST API
- `frontend-v2/` — Phaser 3 程序化像素渲染（無需外部素材）
- `cli/` — 命令列工具
- `tests/` — 完整測試覆蓋（117+ tests）

**⚠ 新功能請在 V2 架構上開發，V1 僅做維護。**

---

## 技術架構（V2）

| 層級 | 技術 | 檔案 |
|------|------|------|
| 核心引擎 | Python 3.10+ | `core/agent.py`, `core/office.py`, `core/store.py`, `core/history.py`, `core/scenes.py` |
| API 伺服器 | Flask 3.0+ (port 19200) | `server/app.py` |
| 前端 | Phaser 3.60 (Canvas) | `frontend-v2/index.html`, `frontend-v2/office-scene.js` |
| CLI | Python argparse | `cli/main.py` |
| 測試 | pytest | `tests/test_agent.py`, `test_office.py`, `test_server.py` |
| 套件管理 | uv | `pyproject.toml` + `uv.lock` |

---

## 目錄結構

```
Star-Office-UI/
├── core/                    # ⭐ V2 核心引擎
│   ├── agent.py             # Agent 類：狀態機 + TTL + display_name + avatar
│   ├── office.py            # Office 管理：多代理人 + JSON 持久化
│   ├── store.py             # JSON 讀寫工具
│   ├── history.py           # JSONL 歷史紀錄 + 每日摘要 + 日誌清理
│   └── scenes.py            # 場景/主題系統（5 種內建場景 + 深淺模式）
│
├── server/                  # ⭐ V2 Flask API (port 19200)
│   └── app.py               # REST 端點 + 前端靜態檔案服務
│
├── frontend-v2/             # ⭐ V2 Phaser 前端
│   ├── index.html           # 主頁面 + 設定 Modal
│   ├── office-scene.js      # Phaser 場景：程序化像素角色渲染
│   └── fonts/               # → ../frontend/fonts (symlink)
│
├── cli/                     # ⭐ V2 命令列工具
│   └── main.py              # star-office add/remove/set/list/status/reset
│
├── tests/                   # ⭐ 測試套件 (117+ tests)
│   ├── test_agent.py        # Agent 模型測試
│   ├── test_office.py       # Office 管理測試
│   ├── test_server.py       # API 端點測試（含 profile/avatar）
│   ├── test_agents.py       # V2 backend 代理人 API 測試
│   ├── test_tasks.py        # 任務管理測試
│   ├── test_history.py      # 歷史紀錄測試
│   └── conftest.py          # 共用 fixtures
│
├── backend/                 # V1 舊版（維護模式）
│   ├── app.py               # 單體 Flask (~2,000 LOC, port 19000)
│   ├── app_v2.py            # Flask-SocketIO 變體
│   ├── models/              # SQLite ORM
│   ├── routes/              # 藍圖路由
│   └── requirements.txt
│
├── frontend/                # V1 舊版前端
│   ├── index.html, game.js, layout.js
│   ├── fonts/               # ArkPixel 像素字體
│   └── *.webp, *.png        # Sprite 素材
│
├── frontend-vue/            # Vue 3 SPA（實驗性，可選）
├── desktop-pet/             # Tauri 桌面小工具
├── electron-shell/          # Electron 封裝
├── scripts/                 # 輔助腳本
│   ├── ai-office-bridge.py  # AI CLI 狀態橋接
│   ├── smoke_test.py
│   └── security_check.py
├── docs/                    # 文件
│   ├── ROADMAP.md           # 開發藍圖
│   ├── DEVELOPMENT.md       # 技術指南
│   └── DEVELOPMENT-V2.md    # V2 架構指南
├── assets/                  # 靜態素材（勿修改）
├── PROJECT_PLAN.md          # 完整專案規劃書
└── todo.md                  # 當前工作清單
```

---

## 快速啟動

```bash
# V2 新版（推薦）
python3 -m pip install flask
python3 server/app.py
# → http://127.0.0.1:19200 （前端 UI + API）

# CLI 工具
python3 cli/main.py add claude "Claude Code"
python3 cli/main.py set claude writing "正在寫程式"
python3 cli/main.py list

# 執行測試
python3 -m pytest tests/ -v

# V1 舊版
cd backend && python3 app.py
# → http://127.0.0.1:19000
```

---

## V2 API 端點（Port 19200）

### Agent 管理

| 方法 | 路徑 | 用途 | 請求 Body |
|------|------|------|-----------|
| GET | `/agents` | 列出所有代理人 | — |
| GET | `/agents/<id>` | 取得單一代理人 | — |
| POST | `/agents` | 新增代理人 | `{"id", "name", "display_name?", "avatar?", "ttl?"}` |
| DELETE | `/agents/<id>` | 移除代理人 | — |

### 狀態控制

| 方法 | 路徑 | 用途 | 請求 Body |
|------|------|------|-----------|
| POST | `/agents/<id>/state` | 設定狀態 | `{"state", "message?"}` |

### Profile 客製化

| 方法 | 路徑 | 用途 | 請求 Body |
|------|------|------|-----------|
| POST | `/agents/<id>/profile` | 更新暱稱/頭像 | `{"display_name?", "avatar?"}` |
| GET | `/avatars` | 列出可用頭像 | — |

### 場景與主題（Phase 6）

| 方法 | 路徑 | 用途 | 請求 Body |
|------|------|------|-----------|
| GET | `/scenes` | 列出可用場景 + 目前場景 | — |
| GET | `/scenes/current` | 取得當前場景（含色彩、區域） | — |
| POST | `/scenes/current` | 切換場景 | `{"scene_id"}` |
| GET | `/theme` | 取得深淺模式狀態 | — |
| POST | `/theme` | 切換深色/淺色模式 | `{"dark_mode": bool}` |
| GET | `/resolution` | 取得畫布解析度 | — |
| POST | `/resolution` | 設定畫布解析度 | `{"width", "height"}` |

### 每日摘要（Phase 6）

| 方法 | 路徑 | 用途 | 參數 |
|------|------|------|------|
| GET | `/agents/<id>/daily-summary` | 單一 agent 每日摘要 | `?date=YYYY-MM-DD` |
| GET | `/daily-summary` | 所有 agent 每日摘要 | `?date=YYYY-MM-DD` |

### 系統

| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/` | 前端 UI（Phaser 畫面） |
| GET | `/health` | 健康檢查 |
| GET | `/api/status` | JSON 概覽（agent 數量、狀態） |
| GET | `/ui/<path>` | 前端靜態檔案 |

---

## Agent 資料模型

```python
Agent:
    id: str              # 唯一識別碼（英數字）
    name: str            # 原始名稱（如 "Claude Code"）
    display_name: str    # 自訂暱稱（如 "Agent K"），空字串時 fallback 到 name
    label: str           # (唯讀) 實際顯示名稱 = display_name or name
    avatar: str          # 頭像 key（如 "char_red"）或自訂圖片路徑
    state: str           # idle | writing | researching | executing | syncing | error
    message: str         # 目前工作描述
    ttl: int             # 工作狀態超時秒數（預設 300）
    last_updated: float  # 最後更新時間戳
    created_at: float    # 建立時間戳
```

### 可用頭像（8 種像素角色）

`char_blue`, `char_green`, `char_red`, `char_purple`, `char_orange`, `char_cyan`, `char_pink`, `char_yellow`

### 狀態機規則

| 狀態 | 類別 | UI 位置 | 圖示 | TTL |
|------|------|---------|------|-----|
| `idle` | 休息 | 🛋 休息區 Lounge | 💤 | 不適用 |
| `writing` | 工作 | 💻 工作區 Workspace | ✍️ | 300s 後自動回 idle |
| `researching` | 工作 | 💻 工作區 Workspace | 🔍 | 300s 後自動回 idle |
| `executing` | 工作 | 💻 工作區 Workspace | ⚡ | 300s 後自動回 idle |
| `syncing` | 工作 | 💻 工作區 Workspace | 🔄 | 300s 後自動回 idle |
| `error` | 錯誤 | 🐛 Debug Corner | 🐛 | 不適用 |

---

## 前端 UI（frontend-v2）

### 技術特點
- **Phaser 3.60** 像素遊戲引擎，`pixelArt: true`
- **Canvas 尺寸**：960×540，自動縮放適應視窗
- **輪詢頻率**：每 3 秒 fetch `/agents`
- **程序化渲染**：像素角色用 Graphics API 即時繪製（無需 sprite 圖片）
- **字體**：ArkPixel（中文像素字體）

### Agent Card 設計
- 200×180px 卡片，邊框顏色依狀態變化
- 程序化 32×52px 像素角色（膚色 + avatar 顏色 body + 狀態動作）
- 顯示：label（暱稱）、狀態標籤、工作訊息、#id
- 左上角 ⚙ 齒輪按鈕 → 開啟設定 Modal
- 工作狀態圖示有脈衝動畫

### 設定 Modal
- 修改 `display_name`（顯示暱稱）
- 選擇 `avatar`（8 種顏色角色 grid）
- 自訂頭像路徑輸入框
- 即時儲存到 API

### 區域配置
- **左側**：休息區 — idle 狀態的 agent
- **中間**：工作區 — writing/researching/executing/syncing
- **右側**：Debug Corner — error 狀態

### 場景系統（Phase 6）
- **右下角控制列**：場景選擇 + 深淺模式切換 + 解析度設定
- **5 種內建場景**：辦公室（預設）、咖啡廳、太空站、花園、圖書館
- 每個場景有獨立的色彩方案和區域標籤
- 深色/淺色模式會覆蓋背景色但保留場景主題色
- 解析度支援 640×360 到 1920×1080

---

## 已完成的開發階段

### Phase 1 ✅ 核心引擎（core/ + cli/）
- Agent 狀態機（6 狀態 + TTL 自動回歸）
- Office 多代理人管理 + JSON 持久化
- CLI 命令列工具
- 17 單元測試

### Phase 2 ✅ Flask REST API（server/）
- 完整 CRUD：新增/刪除/查詢 agent
- 狀態設定 + TTL 自動檢查
- Port 19200（避免與 V1 的 19000 衝突）
- 14 API 測試

### Phase 3 ✅ 前端 UI + 客製化
- Phaser 3 像素辦公室儀表板
- Agent profile 客製化（display_name 暱稱 + avatar 頭像）
- 設定 Modal（⚙ 按鈕）
- API: `POST /agents/<id>/profile`, `GET /avatars`
- 8 種程序化像素角色
- 即時狀態輪詢 + 區域自動分配
- 新增 8 Profile/Avatar 測試

### Phase 4 ✅ 進階 UI 增強
- 進度條顯示（`progress` 欄位）
- 點擊 agent card 彈出詳情面板（detail panel）
- agent 列表側邊欄（可摺疊）
- 狀態變化 toast 通知
- 縮放控制（zoom in/out）

### Phase 5 ✅ 歷史紀錄
- 狀態歷史 API（`GET /agents/<id>/history`）
- JSONL 日誌持久化（`logs/` 目錄）
- 歷史時間軸 UI
- 工作摘要 API（`GET /agents/<id>/summary`）
- 日誌清理 API（`POST /history/cleanup`）

### Phase 6 ✅ 場景與主題
- 5 種內建場景套裝（辦公室、咖啡廳、太空站、花園、圖書館）
- 場景切換 API + 前端 UI 選擇器
- 深色/淺色模式切換（保留場景主題色）
- 畫布解析度可調（640×360 ~ 1920×1080）
- 每日工作摘要自動產生（`GET /agents/<id>/daily-summary`）
- 增強日誌清理（含詳細報告）
- 53 新測試（場景/主題/解析度/摘要）

---

## 下一步開發計畫

### Phase 7 — OpenClaw 整合
- [ ] OpenClaw 連線設定
- [ ] 從 UI 派發任務給 AI 代理人
- [ ] 任務佇列面板
- [ ] 代理人群組管理

### Phase 8 — 進階功能
- [ ] WebSocket 升級（取代輪詢）
- [ ] 自訂角色上傳（sprite sheet）
- [ ] 雙向訊息通道
- [ ] 歷史搜尋功能

---

## 常用操作範例

```bash
# === 啟動 V2 伺服器 ===
python3 server/app.py
# 瀏覽器開啟 http://127.0.0.1:19200

# === Agent 操作（curl） ===
# 新增 agent（含暱稱和頭像）
curl -X POST http://127.0.0.1:19200/agents \
  -H 'Content-Type: application/json' \
  -d '{"id":"claude","name":"Claude Code","display_name":"Agent K","avatar":"char_purple"}'

# 設定工作狀態
curl -X POST http://127.0.0.1:19200/agents/claude/state \
  -H 'Content-Type: application/json' \
  -d '{"state":"writing","message":"重構 API"}'

# 修改暱稱
curl -X POST http://127.0.0.1:19200/agents/claude/profile \
  -H 'Content-Type: application/json' \
  -d '{"display_name":"K 助手","avatar":"char_red"}'

# 查看全部
curl http://127.0.0.1:19200/api/status

# === CLI 操作 ===
python3 cli/main.py add claude "Claude Code"
python3 cli/main.py set claude writing "正在開發新功能"
python3 cli/main.py list

# === 測試 ===
python3 -m pytest tests/ -v              # 全部測試
python3 -m pytest tests/test_server.py -v # 只測 API
```

---

## V1 舊版 API（Port 19000，維護模式）

| 方法 | 路徑 | 用途 |
|------|------|------|
| GET | `/` | 主畫面 |
| GET | `/health` | 健康檢查 |
| GET | `/status` | 取得主代理狀態 |
| POST | `/set_state` | 更新主代理狀態 |
| GET | `/agents` | 列出所有代理人 |
| POST | `/join-agent` | 訪客加入辦公室 |
| POST | `/agent-push` | 訪客推送狀態 |
| POST | `/leave-agent` | 訪客離開 |
| GET | `/yesterday-memo` | 取得昨日備忘 |

---

## AI CLI 橋接（`scripts/ai-office-bridge.py`）

統一橋接腳本，支援 Claude Code / Gemini CLI / Codex CLI：

```bash
export STAR_OFFICE_URL="http://127.0.0.1:19200"
export STAR_OFFICE_JOIN_KEY="ocj_starteam01"

# Claude Code hooks 模式
python3 scripts/ai-office-bridge.py claude-code hook < hook-event.json

# 手動推送狀態
python3 scripts/ai-office-bridge.py claude-code writing "正在編輯程式碼"
```

---

## 關鍵設定檔

| 檔案 | 用途 | 版控 |
|------|------|------|
| `pyproject.toml` | Python 專案設定 | ✅ |
| `office-state.json` | V2 agent 狀態持久化 | ❌ 自動產生 |
| `scene-config.json` | 場景/主題/解析度設定 | ❌ 自動產生 |
| `.env` | 環境變數 | ❌ 參考 `.env.example` |
| `state.json` | V1 主代理狀態 | ❌ |
| `join-keys.json` | 訪客加入金鑰 | ❌ |
| `runtime-config.json` | Gemini API 設定 | ❌ |
| `agents-state.json` | V1 代理人狀態 | ❌ |

---

## 編碼慣例

- **後端**：Python 3.10+，型別提示，docstring
- **前端**：原生 JavaScript + Phaser 3（**不引入框架**）
- **測試**：pytest，每個模組對應一個 test 檔案
- **素材格式**：WebP 優先；透明用 PNG；動畫用 sprite sheet
- **語言**：支援中/英/日三語
- **Port**：V2 用 19200，V1 用 19000（不要互換）

---

## 不要做的事

- 不要修改 `assets/` 下的美術素材檔案（非商業授權）
- 不要將 `.env`、`state.json`、`join-keys.json`、`runtime-config.json`、`agents-state.json`、`office-state.json`、`scene-config.json` 加入版控
- 不要在前端引入額外的打包工具或框架（保持原生 JS + Phaser）
- 不要把 V2 的 port 改回 19000（會與舊版衝突）
- 不要在 V1 backend/app.py 上開發新功能（新功能走 V2）
- 不要刪除 V1 的程式碼（仍有使用者在用）

---

## 關鍵開發文件

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | AI 開發者規範（本文件） |
| `PROJECT_PLAN.md` | 完整專案規劃書（願景、角色、場景設計） |
| `docs/ROADMAP.md` | 開發藍圖與任務清單 |
| `docs/DEVELOPMENT.md` | V1 技術架構指南 |
| `docs/DEVELOPMENT-V2.md` | V2 架構指南 |
| `todo.md` | 當前工作進度 |
| `SKILL.md` | OpenClaw Skill 部署指引 |

---

## 安全注意事項

- **正式環境**必須設定 `STAR_OFFICE_ENV=production`
- `FLASK_SECRET_KEY` 需 ≥24 字元且非弱密碼
- `ASSET_DRAWER_PASS` 需 ≥8 字元（預設 `1234` 僅限開發用）
- 每日備忘錄會自動脫敏 PII（email、電話、路徑、IP）
- 公開存取建議使用 Cloudflare Tunnel + HTTPS
