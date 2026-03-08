"""Tests for Task API endpoints."""


class TestTaskAPI:
    """Test task CRUD and lifecycle."""

    def _create_worker(self, client, name="Worker1"):
        resp = client.post("/api/agents", json={"name": name, "source": "test"})
        return resp.get_json()["agent"]["id"]

    def test_create_task(self, client):
        resp = client.post("/api/tasks", json={
            "title": "Implement login",
            "description": "Add OAuth2 login",
            "priority": "high",
            "createdBy": "agent_openclaw",
        })
        assert resp.status_code == 201
        task = resp.get_json()["task"]
        assert task["title"] == "Implement login"
        assert task["status"] == "pending"
        assert task["priority"] == "high"
        assert task["created_by"] == "agent_openclaw"

    def test_create_task_missing_title(self, client):
        resp = client.post("/api/tasks", json={"createdBy": "agent_openclaw"})
        assert resp.status_code == 400

    def test_list_tasks(self, client):
        client.post("/api/tasks", json={"title": "Task A", "createdBy": "agent_openclaw"})
        client.post("/api/tasks", json={"title": "Task B", "createdBy": "agent_openclaw"})

        resp = client.get("/api/tasks")
        assert resp.status_code == 200
        tasks = resp.get_json()["tasks"]
        assert len(tasks) == 2

    def test_list_tasks_filter_status(self, client):
        client.post("/api/tasks", json={"title": "Task A", "createdBy": "agent_openclaw"})
        resp = client.get("/api/tasks?status=pending")
        assert len(resp.get_json()["tasks"]) == 1

        resp = client.get("/api/tasks?status=completed")
        assert len(resp.get_json()["tasks"]) == 0

    def test_assign_task(self, client):
        worker_id = self._create_worker(client)
        resp = client.post("/api/tasks", json={"title": "Assign me", "createdBy": "agent_openclaw"})
        task_id = resp.get_json()["task"]["id"]

        resp = client.post(f"/api/tasks/{task_id}/assign", json={"agentId": worker_id})
        assert resp.status_code == 200
        task = resp.get_json()["task"]
        assert task["assigned_to"] == worker_id
        assert task["status"] == "assigned"

    def test_update_task_status(self, client):
        resp = client.post("/api/tasks", json={"title": "Status test", "createdBy": "agent_openclaw"})
        task_id = resp.get_json()["task"]["id"]

        resp = client.post(f"/api/tasks/{task_id}/status", json={
            "status": "in_progress",
            "progress": 50,
        })
        assert resp.status_code == 200
        task = resp.get_json()["task"]
        assert task["status"] == "in_progress"
        assert task["progress"] == 50
        assert task["started_at"] is not None

    def test_complete_task(self, client):
        resp = client.post("/api/tasks", json={"title": "Complete me", "createdBy": "agent_openclaw"})
        task_id = resp.get_json()["task"]["id"]

        resp = client.post(f"/api/tasks/{task_id}/status", json={
            "status": "completed",
            "result": "All done!",
        })
        task = resp.get_json()["task"]
        assert task["status"] == "completed"
        assert task["result"] == "All done!"
        assert task["completed_at"] is not None

    def test_subtasks(self, client):
        # Create parent
        resp = client.post("/api/tasks", json={"title": "Parent", "createdBy": "agent_openclaw"})
        parent_id = resp.get_json()["task"]["id"]

        # Create subtasks
        client.post("/api/tasks", json={
            "title": "Subtask 1",
            "createdBy": "agent_openclaw",
            "parentTaskId": parent_id,
        })
        client.post("/api/tasks", json={
            "title": "Subtask 2",
            "createdBy": "agent_openclaw",
            "parentTaskId": parent_id,
        })

        # Get subtasks
        resp = client.get(f"/api/tasks/{parent_id}/subtasks")
        assert resp.status_code == 200
        subtasks = resp.get_json()["subtasks"]
        assert len(subtasks) == 2

    def test_get_task_tree(self, client):
        resp = client.post("/api/tasks", json={"title": "Tree Root", "createdBy": "agent_openclaw"})
        parent_id = resp.get_json()["task"]["id"]

        client.post("/api/tasks", json={
            "title": "Tree Child",
            "createdBy": "agent_openclaw",
            "parentTaskId": parent_id,
        })

        resp = client.get(f"/api/tasks/{parent_id}")
        task = resp.get_json()
        assert "subtasks" in task
        assert len(task["subtasks"]) == 1

    def test_invalid_status(self, client):
        resp = client.post("/api/tasks", json={"title": "Bad status", "createdBy": "agent_openclaw"})
        task_id = resp.get_json()["task"]["id"]

        resp = client.post(f"/api/tasks/{task_id}/status", json={"status": "flying"})
        assert resp.status_code == 400
