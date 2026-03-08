"""Tests for ai-office-bridge-v2.py bridge script with V2 API."""

import os
import sys
import json
import subprocess
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.app import app

BRIDGE_SCRIPT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "scripts", "ai-office-bridge-v2.py"
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = str(tmp_path / "test-state.json")
    log_dir = str(tmp_path / "logs")
    scene_config = str(tmp_path / "scene-config.json")
    os.makedirs(log_dir, exist_ok=True)
    monkeypatch.setattr("server.app.STORE_PATH", store)
    monkeypatch.setattr("server.app.LOG_DIR", log_dir)
    monkeypatch.setattr("server.app.SCENE_CONFIG", scene_config)
    app.testing = True
    with app.test_client() as c:
        yield c


class TestBridgeAPIIntegration:
    """Test that the bridge's expected API calls work against the V2 server."""

    def test_auto_register_and_push(self, client):
        """Simulate bridge auto-registering and pushing state."""
        # Step 1: Bridge checks if agent exists (404)
        r = client.get("/agents/claude")
        assert r.status_code == 404

        # Step 2: Bridge auto-registers
        r = client.post("/agents", json={
            "id": "claude", "name": "Claude Code", "avatar": "char_purple"
        })
        assert r.status_code == 201

        # Step 3: Bridge pushes state
        r = client.post("/agents/claude/state", json={
            "state": "writing", "message": "Editing main.py"
        })
        assert r.status_code == 200
        assert r.get_json()["state"] == "writing"
        assert r.get_json()["message"] == "Editing main.py"

    def test_push_various_states(self, client):
        """Bridge pushes different states based on tool usage."""
        client.post("/agents", json={
            "id": "claude", "name": "Claude Code"
        })

        states = [
            ("writing", "Editing server/app.py"),
            ("researching", "Reading codebase"),
            ("executing", "$ python3 -m pytest"),
            ("syncing", "Syncing data"),
            ("idle", ""),
        ]
        for state, msg in states:
            payload = {"state": state}
            if msg:
                payload["message"] = msg
            r = client.post("/agents/claude/state", json=payload)
            assert r.status_code == 200
            assert r.get_json()["state"] == state

    def test_multiple_agents(self, client):
        """Multiple AI tools can register and push independently."""
        agents = [
            ("claude", "Claude Code", "char_purple"),
            ("gemini", "Gemini CLI", "char_green"),
            ("codex", "Codex CLI", "char_orange"),
        ]
        for aid, name, avatar in agents:
            r = client.post("/agents", json={
                "id": aid, "name": name, "avatar": avatar
            })
            assert r.status_code == 201

        # Each pushes different state
        client.post("/agents/claude/state", json={
            "state": "writing", "message": "Editing code"
        })
        client.post("/agents/gemini/state", json={
            "state": "researching", "message": "Web search"
        })
        client.post("/agents/codex/state", json={
            "state": "executing", "message": "Running tests"
        })

        # All visible in status
        r = client.get("/api/status")
        data = r.get_json()
        assert data["agent_count"] == 3
        states = {a["id"]: a["state"] for a in data["agents"]}
        assert states["claude"] == "writing"
        assert states["gemini"] == "researching"
        assert states["codex"] == "executing"

    def test_register_idempotent(self, client):
        """Registering same agent twice returns 409 (bridge handles this)."""
        client.post("/agents", json={"id": "claude", "name": "Claude Code"})
        r = client.post("/agents", json={"id": "claude", "name": "Claude Code"})
        assert r.status_code == 409

    def test_status_endpoint(self, client):
        """Bridge --status uses GET /api/status."""
        r = client.get("/api/status")
        assert r.status_code == 200
        data = r.get_json()
        assert "agent_count" in data
        assert "agents" in data
        assert "valid_states" in data

    def test_remove_agent(self, client):
        """Bridge --remove uses DELETE /agents/<id>."""
        client.post("/agents", json={"id": "claude", "name": "Claude Code"})
        r = client.delete("/agents/claude")
        assert r.status_code == 200
        r = client.get("/agents/claude")
        assert r.status_code == 404

    def test_state_with_progress(self, client):
        """Bridge can push state with progress."""
        client.post("/agents", json={"id": "claude", "name": "Claude Code"})
        r = client.post("/agents/claude/state", json={
            "state": "executing", "message": "Running tests", "progress": 65
        })
        assert r.status_code == 200
        assert r.get_json()["progress"] == 65

    def test_claude_hook_workflow(self, client):
        """Simulate full Claude Code hook workflow."""
        # Register
        client.post("/agents", json={
            "id": "claude", "name": "Claude Code", "avatar": "char_purple"
        })

        # Simulate tool uses (what bridge does on each hook)
        tool_sequence = [
            ("researching", "Reading codebase"),       # Read tool
            ("writing", "Editing server/app.py"),      # Edit tool
            ("executing", "$ python3 -m pytest"),      # Bash tool
            ("researching", "Web research"),            # WebSearch tool
            ("idle", "任務完成"),                        # Stop hook
        ]
        for state, msg in tool_sequence:
            r = client.post("/agents/claude/state", json={
                "state": state, "message": msg
            })
            assert r.status_code == 200
            assert r.get_json()["state"] == state

        # Final state should be idle
        r = client.get("/agents/claude")
        assert r.get_json()["state"] == "idle"
