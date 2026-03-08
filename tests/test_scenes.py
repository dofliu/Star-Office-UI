"""Tests for Phase 6: Scene/Theme system (core/scenes.py)."""

import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scenes import SceneManager, BUILTIN_SCENES, LIGHT_MODE_OVERRIDES


@pytest.fixture
def scene_manager(tmp_path):
    config_path = str(tmp_path / "scene-config.json")
    return SceneManager(config_path)


class TestBuiltinScenes:
    def test_has_minimum_scenes(self):
        assert len(BUILTIN_SCENES) >= 5

    def test_default_office_exists(self):
        assert "default_office" in BUILTIN_SCENES

    def test_all_scenes_have_required_fields(self):
        required = {"id", "name", "name_en", "name_ja", "description", "colors", "zones"}
        for scene_id, scene in BUILTIN_SCENES.items():
            for field in required:
                assert field in scene, f"Scene '{scene_id}' missing '{field}'"

    def test_all_scenes_have_color_palette(self):
        color_keys = {"bg", "panel", "border", "accent", "floor", "grid", "text", "textDim"}
        for scene_id, scene in BUILTIN_SCENES.items():
            for key in color_keys:
                assert key in scene["colors"], f"Scene '{scene_id}' missing color '{key}'"

    def test_all_scenes_have_zones(self):
        zone_keys = {"lounge", "workspace", "debug"}
        for scene_id, scene in BUILTIN_SCENES.items():
            for key in zone_keys:
                assert key in scene["zones"], f"Scene '{scene_id}' missing zone '{key}'"
                assert "label" in scene["zones"][key]

    def test_scene_ids_match(self):
        for scene_id, scene in BUILTIN_SCENES.items():
            assert scene["id"] == scene_id


class TestSceneManager:
    def test_default_config(self, scene_manager):
        assert scene_manager.config["current_scene"] == "default_office"
        assert scene_manager.config["dark_mode"] is True
        assert scene_manager.config["canvas_width"] == 960
        assert scene_manager.config["canvas_height"] == 540

    def test_get_current_scene(self, scene_manager):
        scene = scene_manager.get_current_scene()
        assert scene["id"] == "default_office"
        assert "colors" in scene
        assert "zones" in scene

    def test_set_scene(self, scene_manager):
        scene = scene_manager.set_scene("cafe")
        assert scene["id"] == "cafe"
        # Verify persistence
        sm2 = SceneManager(scene_manager.config_path)
        assert sm2.config["current_scene"] == "cafe"

    def test_set_invalid_scene(self, scene_manager):
        with pytest.raises(ValueError, match="Unknown scene"):
            scene_manager.set_scene("nonexistent")

    def test_list_scenes(self, scene_manager):
        scenes = scene_manager.list_scenes()
        assert len(scenes) == len(BUILTIN_SCENES)
        ids = [s["id"] for s in scenes]
        assert "default_office" in ids
        assert "cafe" in ids
        assert "space_station" in ids

    def test_list_scenes_format(self, scene_manager):
        scenes = scene_manager.list_scenes()
        for s in scenes:
            assert "id" in s
            assert "name" in s
            assert "name_en" in s
            assert "description" in s
            # Should NOT include full color data in listing
            assert "colors" not in s


class TestDarkLightMode:
    def test_default_is_dark(self, scene_manager):
        assert scene_manager.is_dark_mode() is True

    def test_set_light_mode(self, scene_manager):
        scene = scene_manager.set_dark_mode(False)
        assert scene_manager.is_dark_mode() is False
        # Light mode should override bg/panel/text colors
        assert scene["colors"]["bg"] == LIGHT_MODE_OVERRIDES["bg"]
        assert scene["colors"]["panel"] == LIGHT_MODE_OVERRIDES["panel"]
        assert scene["colors"]["text"] == LIGHT_MODE_OVERRIDES["text"]

    def test_light_mode_preserves_accent(self, scene_manager):
        # Get original accent
        original = BUILTIN_SCENES["default_office"]["colors"]["accent"]
        scene = scene_manager.set_dark_mode(False)
        assert scene["colors"]["accent"] == original

    def test_toggle_back_to_dark(self, scene_manager):
        scene_manager.set_dark_mode(False)
        assert scene_manager.is_dark_mode() is False
        scene = scene_manager.set_dark_mode(True)
        assert scene_manager.is_dark_mode() is True
        # Dark mode should have original colors
        assert scene["colors"]["bg"] == BUILTIN_SCENES["default_office"]["colors"]["bg"]

    def test_light_mode_persists(self, scene_manager):
        scene_manager.set_dark_mode(False)
        sm2 = SceneManager(scene_manager.config_path)
        assert sm2.is_dark_mode() is False

    def test_light_mode_with_different_scenes(self, scene_manager):
        scene_manager.set_scene("space_station")
        scene = scene_manager.set_dark_mode(False)
        # Light mode overrides bg
        assert scene["colors"]["bg"] == LIGHT_MODE_OVERRIDES["bg"]
        # But accent should be space station's accent
        assert scene["colors"]["accent"] == BUILTIN_SCENES["space_station"]["colors"]["accent"]


class TestResolution:
    def test_default_resolution(self, scene_manager):
        res = scene_manager.get_resolution()
        assert res["canvas_width"] == 960
        assert res["canvas_height"] == 540

    def test_set_resolution(self, scene_manager):
        result = scene_manager.set_resolution(1280, 720)
        assert result["canvas_width"] == 1280
        assert result["canvas_height"] == 720

    def test_resolution_persists(self, scene_manager):
        scene_manager.set_resolution(1280, 720)
        sm2 = SceneManager(scene_manager.config_path)
        res = sm2.get_resolution()
        assert res["canvas_width"] == 1280
        assert res["canvas_height"] == 720

    def test_resolution_clamped_min(self, scene_manager):
        result = scene_manager.set_resolution(100, 100)
        assert result["canvas_width"] == 640
        assert result["canvas_height"] == 360

    def test_resolution_clamped_max(self, scene_manager):
        result = scene_manager.set_resolution(4000, 3000)
        assert result["canvas_width"] == 1920
        assert result["canvas_height"] == 1080

    def test_various_resolutions(self, scene_manager):
        for w, h in [(640, 360), (800, 450), (960, 540), (1280, 720), (1920, 1080)]:
            result = scene_manager.set_resolution(w, h)
            assert result["canvas_width"] == w
            assert result["canvas_height"] == h
