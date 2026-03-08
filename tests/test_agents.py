"""Tests for Agent API endpoints."""


class TestAgentAPI:
    """Test agent CRUD and state management."""

    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["version"] == "2.0.0"

    def test_list_agents_has_openclaw(self, client):
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.get_json()
        agents = data["agents"]
        assert len(agents) >= 1
        openclaw = next(a for a in agents if a["name"] == "OpenClaw")
        assert openclaw["role"] == "manager"
        assert openclaw["state"] == "idle"

    def test_register_agent(self, client):
        resp = client.post("/api/agents", json={
            "name": "Claude Code Test",
            "role": "worker",
            "source": "claude-code",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["agent"]["name"] == "Claude Code Test"
        assert data["agent"]["role"] == "worker"
        assert data["agent"]["auth_status"] == "approved"
        assert data["rejoined"] is False

    def test_register_duplicate_rejoins(self, client):
        client.post("/api/agents", json={"name": "TestBot", "source": "test"})
        resp = client.post("/api/agents", json={"name": "TestBot", "source": "test"})
        data = resp.get_json()
        assert data["rejoined"] is True

    def test_push_state(self, client):
        # Register
        resp = client.post("/api/agents", json={"name": "Worker1", "source": "test"})
        agent_id = resp.get_json()["agent"]["id"]

        # Push state
        resp = client.post(f"/api/agents/{agent_id}/state", json={
            "state": "writing",
            "detail": "Editing app.py",
            "toolName": "Edit",
        })
        assert resp.status_code == 200
        agent = resp.get_json()["agent"]
        assert agent["state"] == "writing"
        assert agent["detail"] == "Editing app.py"
        assert agent["current_tool"] == "Edit"
        assert agent["area"] == "desk"

    def test_push_state_aliases(self, client):
        resp = client.post("/api/agents", json={"name": "AliasTest"})
        agent_id = resp.get_json()["agent"]["id"]

        # "working" should alias to "writing"
        resp = client.post(f"/api/agents/{agent_id}/state", json={"state": "working"})
        assert resp.get_json()["agent"]["state"] == "writing"

    def test_push_invalid_state(self, client):
        resp = client.post("/api/agents", json={"name": "BadState"})
        agent_id = resp.get_json()["agent"]["id"]

        resp = client.post(f"/api/agents/{agent_id}/state", json={"state": "flying"})
        assert resp.status_code == 400

    def test_agent_leave(self, client):
        resp = client.post("/api/agents", json={"name": "Leaver"})
        agent_id = resp.get_json()["agent"]["id"]

        resp = client.post(f"/api/agents/{agent_id}/leave")
        assert resp.status_code == 200

        resp = client.get(f"/api/agents/{agent_id}")
        assert resp.get_json()["auth_status"] == "offline"

    def test_delete_agent(self, client):
        resp = client.post("/api/agents", json={"name": "Deletee"})
        agent_id = resp.get_json()["agent"]["id"]

        resp = client.delete(f"/api/agents/{agent_id}")
        assert resp.status_code == 200

        resp = client.get(f"/api/agents/{agent_id}")
        assert resp.status_code == 404

    def test_cannot_delete_manager(self, client):
        resp = client.delete("/api/agents/agent_openclaw")
        assert resp.status_code == 403

    def test_legacy_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "state" in data
        assert "detail" in data

    def test_legacy_set_state(self, client):
        resp = client.post("/api/set_state", json={"state": "writing", "detail": "Testing"})
        assert resp.status_code == 200
        assert resp.get_json()["state"] == "writing"

    def test_token_tracking(self, client):
        resp = client.post("/api/agents", json={"name": "TokenBot"})
        agent_id = resp.get_json()["agent"]["id"]

        client.post(f"/api/agents/{agent_id}/state", json={
            "state": "writing",
            "tokenInput": 5000,
            "tokenOutput": 1200,
        })
        client.post(f"/api/agents/{agent_id}/state", json={
            "state": "executing",
            "tokenInput": 3000,
            "tokenOutput": 800,
        })

        resp = client.get(f"/api/agents/{agent_id}")
        agent = resp.get_json()
        assert agent["token_input"] == 8000
        assert agent["token_output"] == 2000

    def test_progress_tracking(self, client):
        resp = client.post("/api/agents", json={"name": "ProgressBot"})
        agent_id = resp.get_json()["agent"]["id"]

        client.post(f"/api/agents/{agent_id}/state", json={
            "state": "writing",
            "progress": 75,
        })

        resp = client.get(f"/api/agents/{agent_id}")
        assert resp.get_json()["progress"] == 75
