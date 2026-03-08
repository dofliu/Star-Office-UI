# CLAUDE.md — Star Office UI

## 專案概述

Star Office UI 是一個像素風格的 AI 辦公室儀表板，在瀏覽器中以 2D 像素遊戲畫面即時呈現 AI 助理/代理人的工作狀態。支援多代理人協作、三語 UI（中/英/日）、AI 生成房間背景（Gemini API），以及桌面小工具封裝（Tauri / Electron）。

## 技術架構

| 層級 | 技術 | 說明 |
|------|------|------|
| 後端 | Flask 3.0.2 (Python 3.10+) | 核心 API 伺服器，預設 port 19000 |
| 前端 | Phaser 3 (Canvas 2D) | 像素遊戲引擎，1280×720 畫布 |
| 桌面封裝 | Tauri 2 / Electron 40 | 透明視窗桌面小工具（選用） |
| 套件管理 | uv (Python) | pyproject.toml + uv.lock |
| 圖片處理 | Pillow 10.4.0 | WebP 轉換、sprite sheet 生成 |

## 目錄結構

```
Star-Office-UI/
├── backend/           # Flask 後端
│   ├── app.py         # 核心應用 (~2,000 LOC)
│   ├── security_utils.py
│   ├── store_utils.py # JSON 持久化
│   ├── memo_utils.py  # 每日備忘錄擷取 & PII 脫敏
│   ├── requirements.txt
│   └── run.sh
├── frontend/          # Phaser 前端
│   ├── index.html     # 主頁面 + CSS
│   ├── game.js        # 遊戲邏輯 (~1,000 LOC)
│   ├── layout.js      # 佈局座標設定
│   ├── join.html      # 訪客加入頁
│   └── fonts/, *.webp, *.png
├── desktop-pet/       # Tauri 桌面小工具
├── electron-shell/    # Electron 桌面封裝
├── scripts/           # 輔助腳本
│   ├── gemini_image_generate.py
│   ├── smoke_test.py
│   └── security_check.py
├── docs/              # 文件 & 更新紀錄
├── assets/            # 靜態素材
├── dist/              # 發行版本
└── *.py               # 根目錄工具腳本
```

## 快速開發啟動

```bash
# 安裝依賴
python3 -m pip install -r backend/requirements.txt

# 建立 state 檔案
cp state.sample.json state.json

# 啟動後端 (http://127.0.0.1:19000)
cd backend && python3 app.py
```

## 常用指令

```bash
# 狀態控制
python3 set_state.py writing "正在寫程式"
python3 set_state.py idle

# 驗證測試
python3 scripts/smoke_test.py --base-url http://127.0.0.1:19000

# 安全檢查
python3 scripts/security_check.py

# 圖片轉換
python3 convert_to_webp.py
python3 gif_to_spritesheet.py
```

## 核心 API 端點

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
| POST | `/asset-editor/auth` | 素材編輯器驗證 |

## 狀態機

代理人狀態對應辦公室位置：

- `idle` → 休息區（沙發）
- `writing` / `researching` / `executing` / `syncing` → 工作區（桌子）
- `error` → Bug 角落

工作狀態在 300 秒（可設定 TTL）無更新後自動回歸 `idle`。

## 多代理人系統

1. 主機端設定 `join-keys.json`（join key 格式：`ocj_xxx`）
2. 訪客執行 `office-agent-push.py`，每 15 秒推送狀態
3. 前端輪詢 `/agents` 渲染所有代理人

## 關鍵設定檔

| 檔案 | 用途 |
|------|------|
| `.env` | 環境變數（參考 `.env.example`）|
| `state.json` | 主代理狀態（由 `set_state.py` 寫入）|
| `join-keys.json` | 訪客加入金鑰（自動生成）|
| `runtime-config.json` | Gemini API 設定（可透過 UI 調整）|
| `asset-positions.json` | 傢俱座標與縮放 |
| `asset-defaults.json` | 預設素材選擇 |
| `agents-state.json` | 所有代理人狀態（自動生成）|

## 安全注意事項

- **正式環境**必須設定 `STAR_OFFICE_ENV=production`
- `FLASK_SECRET_KEY` 需 ≥24 字元且非弱密碼
- `ASSET_DRAWER_PASS` 需 ≥8 字元（預設 `1234` 僅限開發用）
- 正式環境啟動時會自動檢查，未通過則拒絕啟動
- 每日備忘錄會自動脫敏 PII（email、電話、路徑、IP）
- 公開存取建議使用 Cloudflare Tunnel + HTTPS

## 編碼慣例

- **後端**：Python 3.10+，Flask 路由定義在 `app.py`，JSON 檔案操作透過 `store_utils.py`
- **前端**：原生 JavaScript（無框架），Phaser 3 遊戲引擎，佈局常數集中在 `layout.js`
- **素材格式**：優先 WebP（體積小）；需透明度的用 PNG；動畫用 sprite sheet
- **快取策略**：HTML/API 回應 `no-cache`；靜態資源長快取 + 版本時間戳
- **語言**：支援中/英/日三語，文字切換透過前端語言按鈕

## 開發藍圖（目標）

目前專案正朝四大目標推進，詳見 `docs/ROADMAP.md`：

1. **即時代理人狀態儀表板** — 所有代理人的狀態、工作內容、進度一覽（P0）
2. **代理人工作歷史紀錄** — 查看每個代理人的過往工作日誌與時間軸（P1）
3. **像素畫面客製化** — 場景切換、解析度調整、人物角色選擇（P1）
4. **OpenClaw 整合** — 透過 OpenClaw 管理、調度其他 AI 代理人（P2）

## 關鍵開發文件

| 文件 | 用途 |
|------|------|
| `CLAUDE.md` | AI 開發者規範（本文件） |
| `docs/ROADMAP.md` | 工作藍圖與任務清單 |
| `docs/DEVELOPMENT.md` | 技術架構與開發指南 |
| `SKILL.md` | OpenClaw Skill 部署指引 |

## AI CLI 橋接（`scripts/ai-office-bridge.py`）

統一橋接腳本，支援 Claude Code / Gemini CLI / Codex CLI 三種 AI 工具即時推送狀態：

```bash
# 環境變數設定
export STAR_OFFICE_URL="http://127.0.0.1:19000"
export STAR_OFFICE_JOIN_KEY="ocj_starteam01"

# Claude Code hooks 模式
python3 scripts/ai-office-bridge.py claude-code hook < hook-event.json

# Codex JSONL 串流模式
codex exec --json "task" 2>&1 | python3 scripts/ai-office-bridge.py codex --stream

# 手動推送狀態
python3 scripts/ai-office-bridge.py claude-code writing "正在編輯程式碼"
```

## 不要做的事

- 不要修改 `assets/` 下的美術素材檔案（非商業授權）
- 不要將 `.env`、`state.json`、`join-keys.json`、`runtime-config.json`、`agents-state.json` 加入版控
- 不要在前端引入額外的打包工具或框架（保持原生 JS + Phaser）
- 不要更改預設 port 19000（已協調避免與 OpenClaw Browser Control 衝突）
