"""JSON file persistence for office state."""

import json
import os
from pathlib import Path

DEFAULT_PATH = "office-state.json"


def save(data: dict, path: str = DEFAULT_PATH) -> None:
    """Atomically write data to JSON file."""
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def load(path: str = DEFAULT_PATH) -> dict:
    """Load data from JSON file. Returns empty dict if not found."""
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)
