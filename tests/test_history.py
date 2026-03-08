"""Tests for History API endpoints."""


class TestHistoryAPI:
    """Test history, logs, and reports."""

    def _setup_agent_with_activity(self, client):
        """Create an agent and push some states to generate logs."""
        resp = client.post("/api/agents", json={"name": "HistoryBot", "source": "test"})
        agent_id = resp.get_json()["agent"]["id"]

        states = [
            ("writing", "Editing file.py", "Edit"),
            ("executing", "Running tests", "Bash"),
            ("researching", "Reading docs", "Read"),
            ("writing", "Fixing bug", "Edit"),
            ("idle", "Done", None),
        ]

        for state, detail, tool in states:
            client.post(f"/api/agents/{agent_id}/state", json={
                "state": state,
                "detail": detail,
                "toolName": tool,
            })

        return agent_id

    def test_agent_logs(self, client):
        agent_id = self._setup_agent_with_activity(client)

        resp = client.get(f"/api/history/agents/{agent_id}/logs?range=1d")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["count"] == 5
        assert len(data["logs"]) == 5

    def test_agent_summary(self, client):
        agent_id = self._setup_agent_with_activity(client)

        resp = client.get(f"/api/history/agents/{agent_id}/summary?range=1d")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["stateDistribution"]) > 0
        assert len(data["toolUsage"]) > 0

    def test_overall_summary(self, client):
        self._setup_agent_with_activity(client)

        resp = client.get("/api/history/summary?range=7d")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "agentSummaries" in data
        assert len(data["agentSummaries"]) >= 1

    def test_agent_report(self, client):
        agent_id = self._setup_agent_with_activity(client)

        # Create and complete a task
        resp = client.post("/api/tasks", json={
            "title": "Report test task",
            "createdBy": "agent_openclaw",
        })
        task_id = resp.get_json()["task"]["id"]
        client.post(f"/api/tasks/{task_id}/assign", json={"agentId": agent_id})
        client.post(f"/api/tasks/{task_id}/status", json={"status": "completed"})

        resp = client.get(f"/api/history/report/{agent_id}?range=30d")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["totalTasks"] == 1
        assert data["completedTasks"] == 1
        assert data["completionRate"] == 100.0
        assert len(data["topTools"]) > 0

    def test_task_history(self, client):
        client.post("/api/tasks", json={"title": "History task 1", "createdBy": "agent_openclaw"})
        client.post("/api/tasks", json={"title": "History task 2", "createdBy": "agent_openclaw"})

        resp = client.get("/api/history/tasks?range=7d")
        assert resp.status_code == 200
        assert resp.get_json()["count"] == 2

    def test_messages(self, client):
        # Post message
        resp = client.post("/api/history/messages", json={
            "fromAgent": "agent_openclaw",
            "content": "Starting work on login module",
            "type": "info",
        })
        assert resp.status_code == 201

        # Get messages
        resp = client.get("/api/history/messages")
        assert resp.status_code == 200
        messages = resp.get_json()["messages"]
        assert len(messages) == 1
        assert messages[0]["content"] == "Starting work on login module"

    def test_messages_require_fields(self, client):
        resp = client.post("/api/history/messages", json={"content": "No from"})
        assert resp.status_code == 400


class TestSceneAPI:
    """Test scene/theme endpoints."""

    def test_list_scenes(self, client):
        resp = client.get("/api/scenes")
        assert resp.status_code == 200
        themes = resp.get_json()["themes"]
        assert len(themes) >= 6
        ids = [t["id"] for t in themes]
        assert "modern-office" in ids
        assert "konoha-village" in ids
        assert "classroom" in ids
        assert "meeting-room" in ids
        assert "resort" in ids

    def test_get_scene(self, client):
        resp = client.get("/api/scenes/modern-office")
        assert resp.status_code == 200
        theme = resp.get_json()
        assert theme["id"] == "modern-office"
        assert "positions" in theme

    def test_get_scene_not_found(self, client):
        resp = client.get("/api/scenes/nonexistent")
        assert resp.status_code == 404
