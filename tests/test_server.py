"""Tests for server/app.py Flask API."""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.app import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    store = str(tmp_path / "test-state.json")
    monkeypatch.setattr("server.app.STORE_PATH", store)
    app.testing = True
    with app.test_client() as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_index_empty(client):
    r = client.get("/")
    data = r.get_json()
    assert data["service"] == "Star Office"
    assert data["agent_count"] == 0


def test_add_agent(client):
    r = client.post("/agents", json={"id": "a1", "name": "Alice"})
    assert r.status_code == 201
    assert r.get_json()["id"] == "a1"


def test_add_agent_missing_fields(client):
    r = client.post("/agents", json={"id": "a1"})
    assert r.status_code == 400


def test_add_duplicate(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    r = client.post("/agents", json={"id": "a1", "name": "Alice2"})
    assert r.status_code == 409


def test_list_agents(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    client.post("/agents", json={"id": "a2", "name": "Bob"})
    r = client.get("/agents")
    assert len(r.get_json()["agents"]) == 2


def test_get_agent(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    r = client.get("/agents/a1")
    assert r.status_code == 200
    assert r.get_json()["name"] == "Alice"


def test_get_agent_not_found(client):
    r = client.get("/agents/nope")
    assert r.status_code == 404


def test_set_state(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    r = client.post("/agents/a1/state", json={"state": "writing", "message": "coding"})
    assert r.status_code == 200
    assert r.get_json()["state"] == "writing"
    assert r.get_json()["message"] == "coding"


def test_set_state_invalid(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    r = client.post("/agents/a1/state", json={"state": "sleeping"})
    assert r.status_code == 400


def test_set_state_not_found(client):
    r = client.post("/agents/nope/state", json={"state": "idle"})
    assert r.status_code == 404


def test_remove_agent(client):
    client.post("/agents", json={"id": "a1", "name": "Alice"})
    r = client.delete("/agents/a1")
    assert r.status_code == 200
    # Verify gone
    r2 = client.get("/agents/a1")
    assert r2.status_code == 404


def test_remove_not_found(client):
    r = client.delete("/agents/nope")
    assert r.status_code == 404


def test_full_workflow(client):
    """End-to-end: add -> set state -> check -> remove."""
    # Add
    client.post("/agents", json={"id": "claude", "name": "Claude Code"})
    client.post("/agents", json={"id": "gemini", "name": "Gemini CLI"})

    # Set states
    client.post("/agents/claude/state", json={"state": "writing", "message": "重構"})
    client.post("/agents/gemini/state", json={"state": "researching", "message": "搜尋"})

    # Index shows both
    r = client.get("/")
    data = r.get_json()
    assert data["agent_count"] == 2
    states = {a["id"]: a["state"] for a in data["agents"]}
    assert states["claude"] == "writing"
    assert states["gemini"] == "researching"

    # Reset one
    client.post("/agents/claude/state", json={"state": "idle"})
    r = client.get("/agents/claude")
    assert r.get_json()["state"] == "idle"

    # Remove one
    client.delete("/agents/gemini")
    r = client.get("/agents")
    assert len(r.get_json()["agents"]) == 1
