#!/usr/bin/env python3
"""
海辛辦公室 - Agent 狀態主動推送指令碼

用法：
1. 填入下面的 JOIN_KEY（你從海辛那裡拿到的一次性 join key）
2. 填入 AGENT_NAME（你想要在辦公室裡顯示的名字）
3. 執行：python office-agent-push.py
4. 指令碼會自動先 join（首次執行），然後每 30s 向海辛辦公室推送一次你的當前狀態
"""

import json
import os
import time
import sys
from datetime import datetime

# === 你需要填入的資訊 ===
JOIN_KEY = ""   # 必填：你的一次性 join key
AGENT_NAME = "" # 必填：你在辦公室裡的名字
OFFICE_URL = "https://office.hyacinth.im"  # 海辛辦公室地址（一般不用改）

# === 推送配置 ===
PUSH_INTERVAL_SECONDS = 15  # 每隔多少秒推送一次（更實時）
STATUS_ENDPOINT = "/status"
JOIN_ENDPOINT = "/join-agent"
PUSH_ENDPOINT = "/agent-push"

# 自動狀態守護：當本地狀態檔案不存在或長期不更新時，自動回 idle，避免“假工作中”
STALE_STATE_TTL_SECONDS = int(os.environ.get("OFFICE_STALE_STATE_TTL", "600"))

# 本地狀態儲存（記住上次 join 拿到的 agentId）
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "office-agent-state.json")

# 優先讀取本機 OpenClaw 工作區的狀態檔案（更貼合 AGENTS.md 的工作流）
# 支援自動發現，減少對方手動配置成本。
DEFAULT_STATE_CANDIDATES = [
    "/root/.openclaw/workspace/Star-Office-UI/state.json",  # 當前倉庫（大小寫精確）
    "/root/.openclaw/workspace/star-office-ui/state.json",  # 歷史/相容路徑
    "/root/.openclaw/workspace/state.json",
    os.path.join(os.getcwd(), "state.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json"),
]

# 如果對方本地 /status 需要鑑權，可在這裡填寫 token（或透過環境變數 OFFICE_LOCAL_STATUS_TOKEN）
LOCAL_STATUS_TOKEN = os.environ.get("OFFICE_LOCAL_STATUS_TOKEN", "")
LOCAL_STATUS_URL = os.environ.get("OFFICE_LOCAL_STATUS_URL", "http://127.0.0.1:19000/status")
# 可選：直接指定本地狀態檔案路徑（最簡單方案：繞過 /status 鑑權）
LOCAL_STATE_FILE = os.environ.get("OFFICE_LOCAL_STATE_FILE", "")
VERBOSE = os.environ.get("OFFICE_VERBOSE", "0") in {"1", "true", "TRUE", "yes", "YES"}


def load_local_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "agentId": None,
        "joined": False,
        "joinKey": JOIN_KEY,
        "agentName": AGENT_NAME
    }


def save_local_state(data):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_state(s):
    """相容不同本地狀態詞，並對映到辦公室識別狀態。"""
    s = (s or "").strip().lower()
    if s in {"writing", "researching", "executing", "syncing", "error", "idle"}:
        return s
    if s in {"working", "busy", "write"}:
        return "writing"
    if s in {"run", "running", "execute", "exec"}:
        return "executing"
    if s in {"research", "search"}:
        return "researching"
    if s in {"sync"}:
        return "syncing"
    return "idle"


def map_detail_to_state(detail, fallback_state="idle"):
    """當只有 detail 時，用關鍵詞推斷狀態（貼近 AGENTS.md 的辦公區邏輯）。"""
    d = (detail or "").lower()
    if any(k in d for k in ["報錯", "error", "bug", "異常", "報警"]):
        return "error"
    if any(k in d for k in ["同步", "sync", "備份"]):
        return "syncing"
    if any(k in d for k in ["調研", "research", "搜尋", "查資料"]):
        return "researching"
    if any(k in d for k in ["執行", "run", "推進", "處理任務", "工作中", "writing"]):
        return "writing"
    if any(k in d for k in ["待命", "休息", "idle", "完成", "done"]):
        return "idle"
    return fallback_state


def _state_age_seconds(data):
    try:
        ts = (data or {}).get("updated_at")
        if not ts:
            return None
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if dt.tzinfo is not None:
            from datetime import timezone
            return (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()
        return (datetime.now() - dt).total_seconds()
    except Exception:
        return None


def fetch_local_status():
    """讀取本地狀態：
    1) 優先 state.json（符合 AGENTS.md：任務前切 writing，完成後切 idle）
    2) 其次嘗試本地 HTTP /status
    3) 最後 fallback idle

    額外防抖：如果本地狀態更新時間超過 STALE_STATE_TTL_SECONDS，自動視為 idle。
    """
    # 1) 讀本地 state.json（優先讀取顯式指定路徑，其次自動發現）
    candidate_files = []
    if LOCAL_STATE_FILE:
        candidate_files.append(LOCAL_STATE_FILE)
    for fp in DEFAULT_STATE_CANDIDATES:
        if fp not in candidate_files:
            candidate_files.append(fp)

    for fp in candidate_files:
        try:
            if fp and os.path.exists(fp):
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)

                    # 只接受“狀態檔案”結構；避免誤把 office-agent-state.json（僅快取 agentId）當狀態源
                    if not isinstance(data, dict):
                        continue
                    has_state = "state" in data
                    has_detail = "detail" in data
                    if (not has_state) and (not has_detail):
                        continue

                    state = normalize_state(data.get("state", "idle"))
                    detail = data.get("detail", "") or ""
                    # detail 兜底糾偏，確保“工作/休息/報警”能正確落區
                    state = map_detail_to_state(detail, fallback_state=state)

                    # 防止狀態檔案久未更新仍停留在 working 態
                    age = _state_age_seconds(data)
                    if age is not None and age > STALE_STATE_TTL_SECONDS:
                        state = "idle"
                        detail = f"本地狀態超過{STALE_STATE_TTL_SECONDS}s未更新，自動回待命"

                    if VERBOSE:
                        print(f"[status-source:file] path={fp} state={state} detail={detail[:60]}")
                    return {"state": state, "detail": detail}
        except Exception:
            pass

    # 2) 嘗試本地 /status（可能需要鑑權）
    try:
        import requests
        headers = {}
        if LOCAL_STATUS_TOKEN:
            headers["Authorization"] = f"Bearer {LOCAL_STATUS_TOKEN}"
        r = requests.get(LOCAL_STATUS_URL, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            state = normalize_state(data.get("state", "idle"))
            detail = data.get("detail", "") or ""
            state = map_detail_to_state(detail, fallback_state=state)

            age = _state_age_seconds(data)
            if age is not None and age > STALE_STATE_TTL_SECONDS:
                state = "idle"
                detail = f"本地/status 超過{STALE_STATE_TTL_SECONDS}s未更新，自動回待命"

            if VERBOSE:
                print(f"[status-source:http] url={LOCAL_STATUS_URL} state={state} detail={detail[:60]}")
            return {"state": state, "detail": detail}
        # 如果 401，說明需要 token
        if r.status_code == 401:
            return {"state": "idle", "detail": "本地/status需要鑑權（401），請設定 OFFICE_LOCAL_STATUS_TOKEN"}
    except Exception:
        pass

    # 3) 預設 fallback
    if VERBOSE:
        print("[status-source:fallback] state=idle detail=待命中")
    return {"state": "idle", "detail": "待命中"}


def do_join(local):
    import requests
    payload = {
        "name": local.get("agentName", AGENT_NAME),
        "joinKey": local.get("joinKey", JOIN_KEY),
        "state": "idle",
        "detail": "剛剛加入"
    }
    r = requests.post(f"{OFFICE_URL}{JOIN_ENDPOINT}", json=payload, timeout=10)
    if r.status_code in (200, 201):
        data = r.json()
        if data.get("ok"):
            local["joined"] = True
            local["agentId"] = data.get("agentId")
            save_local_state(local)
            print(f"✅ 已加入海辛辦公室，agentId={local['agentId']}")
            return True
    print(f"❌ 加入失敗：{r.text}")
    return False


def do_push(local, status_data):
    import requests
    payload = {
        "agentId": local.get("agentId"),
        "joinKey": local.get("joinKey", JOIN_KEY),
        "state": status_data.get("state", "idle"),
        "detail": status_data.get("detail", ""),
        "name": local.get("agentName", AGENT_NAME)
    }
    r = requests.post(f"{OFFICE_URL}{PUSH_ENDPOINT}", json=payload, timeout=10)
    if r.status_code in (200, 201):
        data = r.json()
        if data.get("ok"):
            area = data.get("area", "breakroom")
            print(f"✅ 狀態已同步，當前區域={area}")
            return True

    # 403/404：拒絕/移除 → 停止推送
    if r.status_code in (403, 404):
        msg = ""
        try:
            msg = (r.json() or {}).get("msg", "")
        except Exception:
            msg = r.text
        print(f"⚠️  訪問拒絕或已移出房間（{r.status_code}），停止推送：{msg}")
        local["joined"] = False
        local["agentId"] = None
        save_local_state(local)
        sys.exit(1)

    print(f"⚠️  推送失敗：{r.text}")
    return False


def main():
    local = load_local_state()

    # 先確認配置是否齊全
    if not JOIN_KEY or not AGENT_NAME:
        print("❌ 請先在指令碼開頭填入 JOIN_KEY 和 AGENT_NAME")
        sys.exit(1)

    # 如果之前沒 join，先 join
    if not local.get("joined") or not local.get("agentId"):
        ok = do_join(local)
        if not ok:
            sys.exit(1)

    # 持續推送
    print(f"🚀 開始持續推送狀態，間隔={PUSH_INTERVAL_SECONDS}秒")
    print("🧭 狀態邏輯：任務中→工作區；待命/完成→休息區；異常→bug區")
    print("🔐 若本地 /status 返回 Unauthorized(401)，請設定環境變數：OFFICE_LOCAL_STATUS_TOKEN 或 OFFICE_LOCAL_STATUS_URL")
    try:
        while True:
            try:
                status_data = fetch_local_status()
                do_push(local, status_data)
            except Exception as e:
                print(f"⚠️  推送異常：{e}")
            time.sleep(PUSH_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n👋 停止推送")
        sys.exit(0)


if __name__ == "__main__":
    main()
