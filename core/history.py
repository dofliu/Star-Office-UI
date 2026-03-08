"""History logger — JSONL-based state change logging for agents."""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_LOG_DIR = "logs"


class HistoryLogger:
    """Logs agent state changes to JSONL files (one file per agent)."""

    def __init__(self, log_dir: str = DEFAULT_LOG_DIR):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)

    def _log_path(self, agent_id: str) -> str:
        return os.path.join(self.log_dir, f"{agent_id}.jsonl")

    def log_state_change(self, agent_id: str, state: str,
                         message: str = "", progress: int = 0,
                         prev_state: str = "") -> dict:
        """Append a state change entry to the agent's log file."""
        entry = {
            "timestamp": time.time(),
            "datetime": datetime.now().isoformat(timespec="seconds"),
            "agent_id": agent_id,
            "state": state,
            "prev_state": prev_state,
            "message": message,
            "progress": progress,
        }
        path = self._log_path(agent_id)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def get_history(self, agent_id: str, hours: int = 24,
                    limit: int = 100) -> list[dict]:
        """Read recent history entries for an agent."""
        path = self._log_path(agent_id)
        if not os.path.exists(path):
            return []

        cutoff = time.time() - (hours * 3600)
        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("timestamp", 0) >= cutoff:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

        # Return most recent first, limited
        entries.sort(key=lambda e: e["timestamp"], reverse=True)
        return entries[:limit]

    def get_summary(self, agent_id: str, hours: int = 24) -> dict:
        """Generate a work summary for an agent over the given time period."""
        entries = self.get_history(agent_id, hours=hours, limit=10000)
        if not entries:
            return {
                "agent_id": agent_id,
                "period_hours": hours,
                "total_entries": 0,
                "state_counts": {},
                "messages": [],
            }

        state_counts: dict[str, int] = {}
        messages: list[str] = []
        for entry in entries:
            st = entry.get("state", "unknown")
            state_counts[st] = state_counts.get(st, 0) + 1
            msg = entry.get("message", "")
            if msg and msg not in messages:
                messages.append(msg)

        return {
            "agent_id": agent_id,
            "period_hours": hours,
            "total_entries": len(entries),
            "state_counts": state_counts,
            "messages": messages[:20],  # cap at 20 unique messages
            "first_activity": entries[-1].get("datetime", ""),
            "last_activity": entries[0].get("datetime", ""),
        }

    def get_all_agents(self) -> list[str]:
        """List all agent IDs that have log files."""
        agents = []
        if not os.path.isdir(self.log_dir):
            return agents
        for fname in os.listdir(self.log_dir):
            if fname.endswith(".jsonl"):
                agents.append(fname[:-6])  # strip .jsonl
        return sorted(agents)

    def cleanup(self, max_age_days: int = 30) -> int:
        """Remove log entries older than max_age_days. Returns count of removed entries."""
        cutoff = time.time() - (max_age_days * 86400)
        total_removed = 0

        if not os.path.isdir(self.log_dir):
            return 0

        for fname in os.listdir(self.log_dir):
            if not fname.endswith(".jsonl"):
                continue
            path = os.path.join(self.log_dir, fname)
            kept = []
            removed = 0
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("timestamp", 0) >= cutoff:
                            kept.append(line)
                        else:
                            removed += 1
                    except json.JSONDecodeError:
                        continue

            if removed > 0:
                with open(path, "w", encoding="utf-8") as f:
                    for line in kept:
                        f.write(line + "\n")
                total_removed += removed

            # Remove empty files
            if not kept and os.path.exists(path):
                os.remove(path)

        return total_removed
