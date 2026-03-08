"""Scene/theme system — predefined office scene presets."""

import json
import os
from pathlib import Path

# Default scenes with color palettes and zone configurations
BUILTIN_SCENES = {
    "default_office": {
        "id": "default_office",
        "name": "辦公室 Office",
        "name_en": "Office",
        "name_ja": "オフィス",
        "description": "預設暗色像素辦公室",
        "colors": {
            "bg": 0x0F0E17,
            "panel": 0x1A1A2E,
            "border": 0x2E2E4A,
            "accent": 0x7F5AF0,
            "floor": 0x16161A,
            "grid": 0x1A1A2E,
            "text": 0xFFFFFE,
            "textDim": 0x94A1B2,
        },
        "zones": {
            "lounge": {"label": "🛋 休息區 Lounge", "x_ratio": 0.1},
            "workspace": {"label": "💻 工作區 Workspace", "x_ratio": 0.5},
            "debug": {"label": "🐛 Debug Corner", "x_ratio": 0.9},
        },
    },
    "cafe": {
        "id": "cafe",
        "name": "咖啡廳 Café",
        "name_en": "Café",
        "name_ja": "カフェ",
        "description": "溫暖的咖啡色調工作空間",
        "colors": {
            "bg": 0x1B130D,
            "panel": 0x2A1F15,
            "border": 0x4A3828,
            "accent": 0xD4915C,
            "floor": 0x1E1610,
            "grid": 0x2A1F15,
            "text": 0xFFF5E6,
            "textDim": 0xA89080,
        },
        "zones": {
            "lounge": {"label": "☕ 吧台 Bar", "x_ratio": 0.1},
            "workspace": {"label": "📝 座位區 Seats", "x_ratio": 0.5},
            "debug": {"label": "🔧 後廚 Kitchen", "x_ratio": 0.9},
        },
    },
    "space_station": {
        "id": "space_station",
        "name": "太空站 Space Station",
        "name_en": "Space Station",
        "name_ja": "宇宙ステーション",
        "description": "科幻風太空站控制室",
        "colors": {
            "bg": 0x050510,
            "panel": 0x0A0A25,
            "border": 0x1A1A4A,
            "accent": 0x00D4FF,
            "floor": 0x08081A,
            "grid": 0x0A0A25,
            "text": 0xE0F0FF,
            "textDim": 0x6080A0,
        },
        "zones": {
            "lounge": {"label": "🛸 休息艙 Quarters", "x_ratio": 0.1},
            "workspace": {"label": "🖥 控制台 Bridge", "x_ratio": 0.5},
            "debug": {"label": "⚠ 維修區 Repair", "x_ratio": 0.9},
        },
    },
    "garden": {
        "id": "garden",
        "name": "花園 Garden",
        "name_en": "Garden",
        "name_ja": "ガーデン",
        "description": "清新自然綠色花園",
        "colors": {
            "bg": 0x0A1A0A,
            "panel": 0x152515,
            "border": 0x2A4A2A,
            "accent": 0x4ADE80,
            "floor": 0x0D1F0D,
            "grid": 0x152515,
            "text": 0xE8FFE8,
            "textDim": 0x70A070,
        },
        "zones": {
            "lounge": {"label": "🌳 樹下 Shade", "x_ratio": 0.1},
            "workspace": {"label": "🌻 花圃 Garden", "x_ratio": 0.5},
            "debug": {"label": "🌧 溫室 Greenhouse", "x_ratio": 0.9},
        },
    },
    "library": {
        "id": "library",
        "name": "圖書館 Library",
        "name_en": "Library",
        "name_ja": "図書館",
        "description": "安靜的古典圖書館",
        "colors": {
            "bg": 0x12100E,
            "panel": 0x1E1A16,
            "border": 0x3A3228,
            "accent": 0xC9A96E,
            "floor": 0x161210,
            "grid": 0x1E1A16,
            "text": 0xFFF8E8,
            "textDim": 0x9A8A70,
        },
        "zones": {
            "lounge": {"label": "📖 閱讀區 Reading", "x_ratio": 0.1},
            "workspace": {"label": "🖊 書桌區 Desks", "x_ratio": 0.5},
            "debug": {"label": "📚 書庫 Stacks", "x_ratio": 0.9},
        },
    },
}

# Light mode variants of color palettes
LIGHT_MODE_OVERRIDES = {
    "bg": 0xF0EEF6,
    "panel": 0xFFFFFF,
    "border": 0xD0D0E0,
    "floor": 0xE8E6F0,
    "grid": 0xE0DDE8,
    "text": 0x1A1A2E,
    "textDim": 0x6B7280,
}


class SceneManager:
    """Manages scene themes and user preferences."""

    def __init__(self, config_path: str = "scene-config.json"):
        self.config_path = config_path
        self.config = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                pass
        return {
            "current_scene": "default_office",
            "dark_mode": True,
            "canvas_width": 960,
            "canvas_height": 540,
        }

    def save(self) -> None:
        tmp = self.config_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.config_path)

    def get_current_scene(self) -> dict:
        scene_id = self.config.get("current_scene", "default_office")
        scene = BUILTIN_SCENES.get(scene_id, BUILTIN_SCENES["default_office"]).copy()
        # Apply light mode overrides if needed
        if not self.config.get("dark_mode", True):
            scene = self._apply_light_mode(scene)
        return scene

    def _apply_light_mode(self, scene: dict) -> dict:
        scene = scene.copy()
        colors = scene["colors"].copy()
        # Keep accent from original theme
        accent = colors["accent"]
        colors.update(LIGHT_MODE_OVERRIDES)
        colors["accent"] = accent
        scene["colors"] = colors
        return scene

    def set_scene(self, scene_id: str) -> dict:
        if scene_id not in BUILTIN_SCENES:
            raise ValueError(
                f"Unknown scene '{scene_id}'. "
                f"Available: {sorted(BUILTIN_SCENES.keys())}"
            )
        self.config["current_scene"] = scene_id
        self.save()
        return self.get_current_scene()

    def set_dark_mode(self, enabled: bool) -> dict:
        self.config["dark_mode"] = enabled
        self.save()
        return self.get_current_scene()

    def set_resolution(self, width: int, height: int) -> dict:
        width = max(640, min(1920, width))
        height = max(360, min(1080, height))
        self.config["canvas_width"] = width
        self.config["canvas_height"] = height
        self.save()
        return {"canvas_width": width, "canvas_height": height}

    def get_resolution(self) -> dict:
        return {
            "canvas_width": self.config.get("canvas_width", 960),
            "canvas_height": self.config.get("canvas_height", 540),
        }

    def is_dark_mode(self) -> bool:
        return self.config.get("dark_mode", True)

    def list_scenes(self) -> list[dict]:
        return [
            {
                "id": s["id"],
                "name": s["name"],
                "name_en": s["name_en"],
                "name_ja": s["name_ja"],
                "description": s["description"],
            }
            for s in BUILTIN_SCENES.values()
        ]
