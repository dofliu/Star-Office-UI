"""Tests for Phase 5: History logging and API (V2)."""

import os
import sys
import time
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.history import HistoryLogger
from server.app import app


# --- HistoryLogger unit tests ---

@pytest.fixture
def logger(tmp_path):
    return HistoryLogger(str(tmp_path / "test-logs"))


def test_log_state_change(logger):
    entry = logger.log_state_change("agent1", "writing", "coding", 50, prev_state="idle")
    assert entry["agent_id"] == "agent1"
    assert entry["state"] == "writing"
    assert entry["prev_state"] == "idle"
    assert entry["message"] == "coding"
    assert entry["progress"] == 50
    assert "timestamp" in entry
    assert "datetime" in entry


def test_log_creates_file(logger):
    logger.log_state_change("agent1", "writing")
    path = logger._log_path("agent1")
    assert os.path.exists(path)


def test_get_history_empty(logger):
    entries = logger.get_history("nonexistent")
    assert entries == []


def test_get_history_returns_entries(logger):
    logger.log_state_change("a1", "idle", prev_state="")
    logger.log_state_change("a1", "writing", "coding", prev_state="idle")
    logger.log_state_change("a1", "idle", prev_state="writing")
    entries = logger.get_history("a1")
    assert len(entries) == 3
    # Most recent first
    assert entries[0]["state"] == "idle"
    assert entries[0]["prev_state"] == "writing"


def test_get_history_respects_limit(logger):
    for i in range(10):
        logger.log_state_change("a1", "writing", f"task {i}")
    entries = logger.get_history("a1", limit=5)
    assert len(entries) == 5


def test_get_history_respects_hours(logger):
    # Log an entry with old timestamp by writing directly
    old_entry = {
        "timestamp": time.time() - 86400 * 2,  # 2 days ago
        "datetime": "2026-03-06T00:00:00",
        "agent_id": "a1", "state": "writing",
        "prev_state": "idle", "message": "old", "progress": 0,
    }
    path = logger._log_path("a1")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(old_entry) + "\n")
    # Add a recent entry
    logger.log_state_change("a1", "executing", "new")
    entries = logger.get_history("a1", hours=24)
    assert len(entries) == 1
    assert entries[0]["state"] == "executing"


def test_get_summary_empty(logger):
    summary = logger.get_summary("nonexistent")
    assert summary["total_entries"] == 0
    assert summary["state_counts"] == {}


def test_get_summary(logger):
    logger.log_state_change("a1", "writing", "task A", prev_state="idle")
    logger.log_state_change("a1", "writing", "task B", prev_state="writing")
    logger.log_state_change("a1", "idle", prev_state="writing")
    summary = logger.get_summary("a1")
    assert summary["total_entries"] == 3
    assert summary["state_counts"]["writing"] == 2
    assert summary["state_counts"]["idle"] == 1
    assert "task A" in summary["messages"]
    assert "task B" in summary["messages"]


def test_get_all_agents(logger):
    logger.log_state_change("alice", "writing")
    logger.log_state_change("bob", "idle")
    agents = logger.get_all_agents()
    assert agents == ["alice", "bob"]


def test_cleanup(logger):
    # Write an old entry
    old_entry = {
        "timestamp": time.time() - 86400 * 40,  # 40 days ago
        "datetime": "2026-01-27T00:00:00",
        "agent_id": "a1", "state": "writing",
        "prev_state": "", "message": "old", "progress": 0,
    }
    path = logger._log_path("a1")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(old_entry) + "\n")
    # Add a recent entry
    logger.log_state_change("a1", "idle")
    removed = logger.cleanup(max_age_days=30)
    assert removed == 1
    entries = logger.get_history("a1", hours=720)
    assert len(entries) == 1
    assert entries[0]["state"] == "idle"


def test_cleanup_removes_empty_files(logger):
    old_entry = {
        "timestamp": time.time() - 86400 * 40,
        "datetime": "2026-01-27T00:00:00",
        "agent_id": "old_agent", "state": "idle",
        "prev_state": "", "message": "", "progress": 0,
    }
    path = logger._log_path("old_agent")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(json.dumps(old_entry) + "\n")
    logger.cleanup(max_age_days=30)
    assert not os.path.exists(path)


# --- Server API integration tests ---

@pytest.fixture
def client(tmp_path, monkeypatch):
    store = str(tmp_path / "test-state.json")
    log_dir = str(tmp_path / "test-logs")
    monkeypatch.setattr("server.app.STORE_PATH", store)
    monkeypatch.setattr("server.app.LOG_DIR", log_dir)
    app.testing = True
    with app.test_client() as c:
        yield c


def _add_agent(client, agent_id="a1", name="Alice"):
    client.post("/agents", json={"id": agent_id, "name": name})


def test_history_api_empty(client):
    r = client.get("/agents/nonexistent/history")
    assert r.status_code == 200
    data = r.get_json()
    assert data["count"] == 0
    assert data["entries"] == []


def test_history_api_after_state_change(client):
    _add_agent(client)
    client.post("/agents/a1/state", json={"state": "writing", "message": "coding"})
    client.post("/agents/a1/state", json={"state": "idle"})
    r = client.get("/agents/a1/history")
    data = r.get_json()
    assert data["count"] == 2
    entries = data["entries"]
    # Most recent first
    assert entries[0]["state"] == "idle"
    assert entries[1]["state"] == "writing"


def test_history_api_with_hours_param(client):
    _add_agent(client)
    client.post("/agents/a1/state", json={"state": "writing"})
    r = client.get("/agents/a1/history?hours=1")
    assert r.status_code == 200
    assert r.get_json()["count"] >= 1


def test_history_api_with_limit_param(client):
    _add_agent(client)
    for i in range(5):
        client.post("/agents/a1/state", json={"state": "writing", "message": f"task {i}"})
    r = client.get("/agents/a1/history?limit=3")
    assert r.get_json()["count"] == 3


def test_summary_api_empty(client):
    r = client.get("/agents/nonexistent/summary")
    assert r.status_code == 200
    data = r.get_json()
    assert data["total_entries"] == 0


def test_summary_api(client):
    _add_agent(client)
    client.post("/agents/a1/state", json={"state": "writing", "message": "A"})
    client.post("/agents/a1/state", json={"state": "researching", "message": "B"})
    client.post("/agents/a1/state", json={"state": "idle"})
    r = client.get("/agents/a1/summary?hours=24")
    data = r.get_json()
    assert data["total_entries"] == 3
    assert "writing" in data["state_counts"]
    assert "researching" in data["state_counts"]


def test_cleanup_api(client):
    r = client.post("/history/cleanup", json={"max_age_days": 30})
    assert r.status_code == 200
    data = r.get_json()
    assert data["max_age_days"] == 30
    assert "removed_entries" in data


def test_history_logs_prev_state(client):
    """Verify prev_state is correctly recorded."""
    _add_agent(client)
    client.post("/agents/a1/state", json={"state": "writing", "message": "first"})
    client.post("/agents/a1/state", json={"state": "researching", "message": "second"})
    r = client.get("/agents/a1/history")
    entries = r.get_json()["entries"]
    # Most recent: researching, prev was writing
    assert entries[0]["state"] == "researching"
    assert entries[0]["prev_state"] == "writing"
    # Earlier: writing, prev was idle (new agent starts idle)
    assert entries[1]["state"] == "writing"
    assert entries[1]["prev_state"] == "idle"


def test_history_with_progress(client):
    """Progress field is recorded in history."""
    _add_agent(client)
    client.post("/agents/a1/state", json={
        "state": "executing", "message": "building", "progress": 75
    })
    r = client.get("/agents/a1/history")
    entries = r.get_json()["entries"]
    assert entries[0]["progress"] == 75
