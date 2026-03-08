"""Tests for Phase 6: Server API endpoints (scenes, themes, resolution, daily summary)."""

import os
import sys
import json
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.app import app


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


# === Scene API Tests ===

class TestSceneAPI:
    def test_list_scenes(self, client):
        r = client.get("/scenes")
        assert r.status_code == 200
        data = r.get_json()
        assert "scenes" in data
        assert "current" in data
        assert len(data["scenes"]) >= 5
        assert data["current"] == "default_office"

    def test_get_current_scene(self, client):
        r = client.get("/scenes/current")
        assert r.status_code == 200
        data = r.get_json()
        assert data["id"] == "default_office"
        assert "colors" in data
        assert "zones" in data

    def test_set_scene(self, client):
        r = client.post("/scenes/current", json={"scene_id": "cafe"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["id"] == "cafe"

    def test_set_scene_persists(self, client):
        client.post("/scenes/current", json={"scene_id": "space_station"})
        r = client.get("/scenes/current")
        assert r.get_json()["id"] == "space_station"

    def test_set_invalid_scene(self, client):
        r = client.post("/scenes/current", json={"scene_id": "mars_base"})
        assert r.status_code == 400

    def test_set_scene_missing_id(self, client):
        r = client.post("/scenes/current", json={})
        assert r.status_code == 400

    def test_scene_has_all_fields(self, client):
        r = client.get("/scenes/current")
        data = r.get_json()
        assert "name" in data
        assert "name_en" in data
        assert "description" in data
        assert "bg" in data["colors"]
        assert "accent" in data["colors"]

    def test_switch_all_scenes(self, client):
        """Cycle through all scenes."""
        r = client.get("/scenes")
        scenes = r.get_json()["scenes"]
        for scene in scenes:
            r = client.post("/scenes/current", json={"scene_id": scene["id"]})
            assert r.status_code == 200
            assert r.get_json()["id"] == scene["id"]


# === Theme API Tests ===

class TestThemeAPI:
    def test_get_theme_default(self, client):
        r = client.get("/theme")
        assert r.status_code == 200
        data = r.get_json()
        assert data["dark_mode"] is True
        assert "scene" in data

    def test_set_light_mode(self, client):
        r = client.post("/theme", json={"dark_mode": False})
        assert r.status_code == 200
        data = r.get_json()
        assert data["dark_mode"] is False

    def test_set_dark_mode(self, client):
        client.post("/theme", json={"dark_mode": False})
        r = client.post("/theme", json={"dark_mode": True})
        assert r.status_code == 200
        assert r.get_json()["dark_mode"] is True

    def test_theme_missing_field(self, client):
        r = client.post("/theme", json={})
        assert r.status_code == 400

    def test_theme_persists(self, client):
        client.post("/theme", json={"dark_mode": False})
        r = client.get("/theme")
        assert r.get_json()["dark_mode"] is False

    def test_light_mode_changes_colors(self, client):
        # Dark mode colors
        r1 = client.get("/scenes/current")
        dark_bg = r1.get_json()["colors"]["bg"]

        # Switch to light mode
        client.post("/theme", json={"dark_mode": False})
        r2 = client.get("/scenes/current")
        light_bg = r2.get_json()["colors"]["bg"]

        assert dark_bg != light_bg


# === Resolution API Tests ===

class TestResolutionAPI:
    def test_get_default_resolution(self, client):
        r = client.get("/resolution")
        assert r.status_code == 200
        data = r.get_json()
        assert data["canvas_width"] == 960
        assert data["canvas_height"] == 540

    def test_set_resolution(self, client):
        r = client.post("/resolution", json={"width": 1280, "height": 720})
        assert r.status_code == 200
        data = r.get_json()
        assert data["canvas_width"] == 1280
        assert data["canvas_height"] == 720

    def test_resolution_persists(self, client):
        client.post("/resolution", json={"width": 1280, "height": 720})
        r = client.get("/resolution")
        data = r.get_json()
        assert data["canvas_width"] == 1280
        assert data["canvas_height"] == 720

    def test_resolution_clamped(self, client):
        r = client.post("/resolution", json={"width": 100, "height": 100})
        data = r.get_json()
        assert data["canvas_width"] >= 640
        assert data["canvas_height"] >= 360

    def test_resolution_missing_fields(self, client):
        r = client.post("/resolution", json={"width": 1280})
        assert r.status_code == 400

    def test_resolution_invalid_type(self, client):
        r = client.post("/resolution", json={"width": "abc", "height": "def"})
        assert r.status_code == 400


# === Daily Summary API Tests ===

class TestDailySummaryAPI:
    def _add_agent_with_history(self, client):
        """Helper: add agent and create some state changes."""
        client.post("/agents", json={"id": "dev", "name": "Developer"})
        client.post("/agents/dev/state", json={
            "state": "writing", "message": "Building feature"
        })
        client.post("/agents/dev/state", json={
            "state": "researching", "message": "Reading docs"
        })
        client.post("/agents/dev/state", json={
            "state": "idle"
        })

    def test_daily_summary_empty(self, client):
        r = client.get("/agents/nobody/daily-summary")
        assert r.status_code == 200
        data = r.get_json()
        assert data["total_entries"] == 0

    def test_daily_summary_with_data(self, client):
        self._add_agent_with_history(client)
        r = client.get("/agents/dev/daily-summary")
        assert r.status_code == 200
        data = r.get_json()
        assert data["agent_id"] == "dev"
        assert data["total_entries"] >= 2
        assert "state_distribution" in data
        assert "tasks" in data

    def test_daily_summary_specific_date(self, client):
        r = client.get("/agents/dev/daily-summary?date=2020-01-01")
        assert r.status_code == 200
        data = r.get_json()
        assert data["total_entries"] == 0  # no data for old date

    def test_daily_summary_invalid_date(self, client):
        r = client.get("/agents/dev/daily-summary?date=not-a-date")
        assert r.status_code == 400

    def test_all_daily_summaries(self, client):
        self._add_agent_with_history(client)
        r = client.get("/daily-summary")
        assert r.status_code == 200
        data = r.get_json()
        assert "summaries" in data

    def test_all_daily_summaries_with_date(self, client):
        r = client.get("/daily-summary?date=2020-01-01")
        assert r.status_code == 200
        data = r.get_json()
        assert len(data["summaries"]) == 0


# === Enhanced Cleanup API Tests ===

class TestEnhancedCleanupAPI:
    def test_cleanup_returns_details(self, client):
        r = client.post("/history/cleanup", json={"max_age_days": 30})
        assert r.status_code == 200
        data = r.get_json()
        assert "removed_entries" in data
        assert "max_age_days" in data
        assert "remaining_agents" in data
        assert "remaining_agent_count" in data


# === Integration Tests ===

class TestPhase6Integration:
    def test_scene_and_theme_combined(self, client):
        """Switch scene then toggle theme."""
        # Set cafe scene
        client.post("/scenes/current", json={"scene_id": "cafe"})
        # Toggle to light mode
        client.post("/theme", json={"dark_mode": False})
        # Verify scene is cafe with light colors
        r = client.get("/scenes/current")
        data = r.get_json()
        assert data["id"] == "cafe"
        # Light mode should change bg
        from core.scenes import LIGHT_MODE_OVERRIDES
        assert data["colors"]["bg"] == LIGHT_MODE_OVERRIDES["bg"]
        # Accent should be cafe's accent
        from core.scenes import BUILTIN_SCENES
        assert data["colors"]["accent"] == BUILTIN_SCENES["cafe"]["colors"]["accent"]

    def test_full_phase6_workflow(self, client):
        """Full workflow: create agent, log history, get summary, switch scene."""
        # Add agent
        client.post("/agents", json={"id": "ai1", "name": "AI One"})
        # Do some work
        client.post("/agents/ai1/state", json={
            "state": "writing", "message": "Phase 6 dev", "progress": 50
        })
        client.post("/agents/ai1/state", json={
            "state": "executing", "message": "Running tests", "progress": 80
        })
        # Get daily summary
        r = client.get("/agents/ai1/daily-summary")
        assert r.status_code == 200
        assert r.get_json()["total_entries"] >= 2
        # Switch scene
        r = client.post("/scenes/current", json={"scene_id": "garden"})
        assert r.status_code == 200
        # Set resolution
        r = client.post("/resolution", json={"width": 1280, "height": 720})
        assert r.status_code == 200
        # Toggle theme
        r = client.post("/theme", json={"dark_mode": False})
        assert r.status_code == 200
        # Everything still works
        r = client.get("/agents/ai1")
        assert r.status_code == 200
        assert r.get_json()["state"] == "executing"
