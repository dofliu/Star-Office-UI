"""
Claw Office UI - Scene Routes

API endpoints for scene/theme management.
"""

import os
import json
from flask import Blueprint, request, jsonify

bp = Blueprint("scenes", __name__, url_prefix="/api")

THEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "frontend-vue", "public", "themes")


def _get_themes_config() -> dict:
    """Load themes configuration."""
    config_path = os.path.join(THEMES_DIR, "themes.json")
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"themes": _default_themes()}


def _default_themes() -> list:
    """Return default themes list."""
    return [
        {
            "id": "modern-office",
            "name": {"zh": "現代辦公室", "en": "Modern Office", "ja": "モダンオフィス"},
            "description": {"zh": "簡潔現代的辦公室空間", "en": "Clean modern office space", "ja": "クリーンなモダンオフィス"},
            "thumbnail": "themes/modern-office/thumb.webp",
            "background": "themes/modern-office/bg.svg",
            "positions": {
                "manager": {"x": 200, "y": 300},
                "workers": [
                    {"x": 450, "y": 250},
                    {"x": 650, "y": 250},
                    {"x": 850, "y": 250},
                    {"x": 450, "y": 450},
                    {"x": 650, "y": 450},
                    {"x": 850, "y": 450},
                ],
                "breakroom": {"x": 1050, "y": 400},
                "error_corner": {"x": 100, "y": 550},
            },
        },
        {
            "id": "konoha-village",
            "name": {"zh": "木葉忍者村", "en": "Konoha Village", "ja": "木ノ葉隠れの里"},
            "description": {"zh": "火影忍者木葉村風格", "en": "Naruto's Konoha Village style", "ja": "ナルトの木ノ葉隠れの里スタイル"},
            "thumbnail": "themes/konoha-village/thumb.webp",
            "background": "themes/konoha-village/bg.svg",
            "positions": {
                "manager": {"x": 200, "y": 280},
                "workers": [
                    {"x": 420, "y": 230},
                    {"x": 620, "y": 230},
                    {"x": 820, "y": 230},
                    {"x": 420, "y": 430},
                    {"x": 620, "y": 430},
                    {"x": 820, "y": 430},
                ],
                "breakroom": {"x": 1050, "y": 380},
                "error_corner": {"x": 100, "y": 530},
            },
        },
        {
            "id": "pixel-classic",
            "name": {"zh": "經典像素辦公室", "en": "Classic Pixel Office", "ja": "クラシックピクセルオフィス"},
            "description": {"zh": "懷舊像素風格辦公室", "en": "Retro pixel-art office", "ja": "レトロピクセルアートオフィス"},
            "thumbnail": "themes/pixel-classic/thumb.webp",
            "background": "themes/pixel-classic/bg.svg",
            "positions": {
                "manager": {"x": 200, "y": 300},
                "workers": [
                    {"x": 450, "y": 250},
                    {"x": 650, "y": 250},
                    {"x": 850, "y": 250},
                    {"x": 450, "y": 450},
                    {"x": 650, "y": 450},
                    {"x": 850, "y": 450},
                ],
                "breakroom": {"x": 1050, "y": 400},
                "error_corner": {"x": 100, "y": 550},
            },
        },
        {
            "id": "classroom",
            "name": {"zh": "教室", "en": "Classroom", "ja": "教室"},
            "description": {"zh": "學校教室風格", "en": "School classroom style", "ja": "学校の教室スタイル"},
            "thumbnail": "themes/classroom/thumb.webp",
            "background": "themes/classroom/bg.svg",
            "positions": {
                "manager": {"x": 640, "y": 120},
                "workers": [
                    {"x": 300, "y": 300},
                    {"x": 500, "y": 300},
                    {"x": 700, "y": 300},
                    {"x": 300, "y": 480},
                    {"x": 500, "y": 480},
                    {"x": 700, "y": 480},
                ],
                "breakroom": {"x": 1050, "y": 400},
                "error_corner": {"x": 100, "y": 580},
            },
        },
        {
            "id": "meeting-room",
            "name": {"zh": "會議室", "en": "Meeting Room", "ja": "会議室"},
            "description": {"zh": "正式會議室風格", "en": "Formal meeting room", "ja": "フォーマルな会議室"},
            "thumbnail": "themes/meeting-room/thumb.webp",
            "background": "themes/meeting-room/bg.svg",
            "positions": {
                "manager": {"x": 640, "y": 150},
                "workers": [
                    {"x": 350, "y": 320},
                    {"x": 550, "y": 320},
                    {"x": 750, "y": 320},
                    {"x": 350, "y": 480},
                    {"x": 550, "y": 480},
                    {"x": 750, "y": 480},
                ],
                "breakroom": {"x": 1080, "y": 400},
                "error_corner": {"x": 100, "y": 560},
            },
        },
        {
            "id": "resort",
            "name": {"zh": "度假村", "en": "Beach Resort", "ja": "ビーチリゾート"},
            "description": {"zh": "海灘度假村風格", "en": "Beach resort style", "ja": "ビーチリゾートスタイル"},
            "thumbnail": "themes/resort/thumb.webp",
            "background": "themes/resort/bg.svg",
            "positions": {
                "manager": {"x": 200, "y": 280},
                "workers": [
                    {"x": 420, "y": 240},
                    {"x": 620, "y": 240},
                    {"x": 820, "y": 240},
                    {"x": 420, "y": 440},
                    {"x": 620, "y": 440},
                    {"x": 820, "y": 440},
                ],
                "breakroom": {"x": 1060, "y": 380},
                "error_corner": {"x": 100, "y": 540},
            },
        },
    ]


@bp.route("/scenes", methods=["GET"])
def list_scenes():
    """List all available scenes/themes."""
    config = _get_themes_config()
    return jsonify({"themes": config.get("themes", _default_themes())})


@bp.route("/scenes/<theme_id>", methods=["GET"])
def get_scene(theme_id):
    """Get scene details."""
    config = _get_themes_config()
    themes = config.get("themes", _default_themes())
    for theme in themes:
        if theme["id"] == theme_id:
            return jsonify(theme)
    return jsonify({"error": "Theme not found"}), 404
