# Star Office UI — 開發指南 (Development Guide)

> 本文件供開發者（包含 Desktop Claude）在本機接續開發時參考。

---

## 快速上手

```bash
# 1. Clone 並切換到開發分支
git clone https://github.com/dofliu/Star-Office-UI.git
cd Star-Office-UI
git checkout claude/analyze-project-docs-BUR8S

# 2. 安裝 Python 依賴
python3 -m pip install -r backend/requirements.txt

# 3. 初始化狀態檔
cp state.sample.json state.json

# 4. 啟動後端 (port 19000)
cd backend && python3 app.py

# 5. 瀏覽器打開
open http://127.0.0.1:19000
```

---

## 專案架構

```
Star-Office-UI/
├── backend/                 # Flask 後端 (Python 3.10+)
│   ├── app.py               # 主應用，所有 API 路由 (~2000 LOC)
│   ├── security_utils.py    # 正式環境安全檢查
│   ├── store_utils.py       # JSON 檔案讀寫抽象層
│   ├── memo_utils.py        # 每日備忘錄 + PII 脫敏
│   └── requirements.txt     # Python 套件依賴
│
├── frontend/                # Phaser 3 前端 (原生 JS)
│   ├── index.html           # 主頁面（含 Asset Editor UI）
│   ├── game.js              # 遊戲主邏輯（角色、動畫、輪詢）
│   ├── layout.js            # 佈局常數（座標、depth、縮放）
│   ├── join.html            # 代理人加入頁面
│   ├── invite.html          # 人類邀請說明頁
│   └── office-agent-push.py # 舊版訪客推送腳本
│
├── scripts/                 # 工具腳本
│   ├── ai-office-bridge.py  # AI CLI 狀態橋接（Claude/Gemini/Codex）
│   ├── smoke_test.py        # API 煙霧測試
│   ├── security_check.py    # 安全掃描
│   └── gemini_image_generate.py  # Gemini 圖片生成
│
├── desktop-pet/             # Tauri 桌面小工具
├── electron-shell/          # Electron 桌面封裝
├── assets/                  # 靜態美術素材（勿修改）
├── docs/                    # 文件目錄
│
├── state.json               # 主代理人狀態（runtime, 不入版控）
├── agents-state.json        # 所有代理人狀態（runtime, 不入版控）
├── join-keys.json           # 加入金鑰（runtime, 不入版控）
├── runtime-config.json      # Gemini 等 API 設定（runtime, 不入版控）
├── asset-positions.json     # 傢俱座標與縮放
├── asset-defaults.json      # 預設素材選擇
│
├── set_state.py             # 快速設定主代理狀態
├── CLAUDE.md                # AI 開發者指南
├── SKILL.md                 # OpenClaw Skill 定義
└── README.md                # 專案說明
```

---

## 核心模組說明

### 後端 (`backend/app.py`)

#### 狀態機
```
idle ─────→ breakroom（休息區/沙發）
writing ──→ writing（工作區/桌子）
researching → writing
executing ─→ writing
syncing ──→ writing
error ────→ error（Bug 角落）
```

工作狀態在 `ttl_seconds`（預設 300 秒）無更新後自動回歸 `idle`。

#### 關鍵 API

| 方法 | 路徑 | 用途 | 驗證 |
|------|------|------|------|
| GET | `/` | 主畫面 | 無 |
| GET | `/health` | 健康檢查 | 無 |
| GET | `/status` | 主代理狀態 | 無 |
| POST | `/set_state` | 更新主代理狀態 | 無 |
| GET | `/agents` | 所有代理人列表 | 無 |
| POST | `/join-agent` | 訪客加入辦公室 | Join Key |
| POST | `/agent-push` | 訪客推送狀態 | agentId + joinKey |
| POST | `/leave-agent` | 訪客離開 | agentId |
| GET | `/yesterday-memo` | 昨日備忘錄 | 無 |
| POST | `/asset-editor/auth` | 素材編輯器登入 | 密碼 |
| POST | `/generate-room` | AI 生成房間背景 | 編輯器驗證 |
| GET | `/list-assets` | 列出可替換素材 | 編輯器驗證 |
| POST | `/replace-asset` | 替換素材檔案 | 編輯器驗證 |

#### 多代理人系統

```
OpenClaw / AI CLI
    │
    ▼
ai-office-bridge.py ──POST /join-agent──→ Flask app.py
    │                                         │
    │ (每次工具呼叫)                           │ (存入 agents-state.json)
    │                                         │
    └──POST /agent-push──────────────────→    │
                                              │
前端 game.js ←──GET /agents（輪詢 3s）────────┘
```

### 前端 (`frontend/`)

#### 技術棧
- **Phaser 3** — Canvas 2D 像素遊戲引擎
- **原生 JavaScript** — 無框架、無打包工具
- **佈局管理** — `layout.js` 集中管理所有座標常數

#### 渲染流程
1. `preload()` — 載入所有 sprite sheet 和背景圖
2. `create()` — 建立場景物件（背景、傢俱、角色）
3. `update()` — 每幀更新角色位置與動畫
4. 輪詢 `/status` 和 `/agents` 更新狀態

#### 目前畫布規格
- 解析度：1280×720（固定）
- 像素風格：`pixelArt: true`
- 訪客角色：6 種動畫 sprite（`guest_anim_1~6.webp`）

### AI CLI 橋接 (`scripts/ai-office-bridge.py`)

支援三種 AI CLI 工具的即時狀態推送：

| CLI | 模式 | 觸發方式 |
|-----|------|----------|
| Claude Code | Hook 事件 | `.claude/settings.json` 中的 hooks |
| Gemini CLI | Hook 事件 | Gemini hooks 設定 |
| Codex CLI | JSONL 串流 | `codex exec --json \| python3 ai-office-bridge.py codex --stream` |

設定環境變數：
```bash
export STAR_OFFICE_URL="http://127.0.0.1:19000"
export STAR_OFFICE_JOIN_KEY="ocj_starteam01"
```

---

## 開發規範

### 必須遵守
- **不要修改 `assets/`** 下的美術素材（非商業授權）
- **不要將 runtime 檔案加入版控**（`.env`, `state.json`, `join-keys.json`, `runtime-config.json`, `agents-state.json`）
- **不要引入前端打包工具或框架**（保持原生 JS + Phaser）
- **不要更改預設 port 19000**
- **三語支援**：新增 UI 文字需提供中/英/日翻譯

### 建議遵守
- 後端新路由加在 `app.py` 中（目前為單檔架構）
- JSON 檔案操作透過 `store_utils.py`
- 佈局相關常數加在 `layout.js`
- 素材格式：優先 WebP → 需透明度用 PNG → 動畫用 sprite sheet

### 測試

```bash
# 煙霧測試（後端需先啟動）
python3 scripts/smoke_test.py --base-url http://127.0.0.1:19000

# 安全檢查
python3 scripts/security_check.py

# 手動測試狀態切換
python3 set_state.py writing "測試工作狀態"
python3 set_state.py idle
```

---

## 接下來要做什麼

請參考 `docs/ROADMAP.md` 的開發階段規劃：

1. **Phase 1**（基礎增強）— 進度條、代理人面板、通知
2. **Phase 2**（歷史與客製化）— 狀態日誌、歷史面板、人物選擇
3. **Phase 3**（場景與主題）— 場景套裝、深色模式
4. **Phase 4**（OpenClaw 整合）— 連線設定、任務調度

每個 Phase 的具體任務清單見 ROADMAP.md。

---

## 常見問題

### Q: 啟動後看不到訪客？
A: 確認有執行 `ai-office-bridge.py` 並設定 `STAR_OFFICE_JOIN_KEY`。首次需要有 `join-keys.json`（後端會自動生成預設 keys）。

### Q: 背景圖替換後沒有生效？
A: 靜態資源有長快取。嘗試硬重新整理（Ctrl+Shift+R），或重啟後端（會產生新的 `VERSION_TIMESTAMP`）。

### Q: Desktop Claude 怎麼接續？
A: 在本機 `git checkout claude/analyze-project-docs-BUR8S`，閱讀 `CLAUDE.md` + `docs/ROADMAP.md`，從 Phase 1 開始開發。
