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

    def generate_daily_summary(self, agent_id: str, date_str: str = "") -> dict:
        """Generate a daily work summary for a specific date (YYYY-MM-DD).
        If date_str is empty, uses today's date."""
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return {"error": f"Invalid date format: {date_str}. Use YYYY-MM-DD."}

        start_ts = target_date.replace(hour=0, minute=0, second=0).timestamp()
        end_ts = target_date.replace(hour=23, minute=59, second=59).timestamp()

        path = self._log_path(agent_id)
        if not os.path.exists(path):
            return {
                "agent_id": agent_id,
                "date": date_str,
                "total_entries": 0,
                "work_time_minutes": 0,
                "state_distribution": {},
                "tasks": [],
                "first_activity": "",
                "last_activity": "",
            }

        entries = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("timestamp", 0)
                    if start_ts <= ts <= end_ts:
                        entries.append(entry)
                except json.JSONDecodeError:
                    continue

        if not entries:
            return {
                "agent_id": agent_id,
                "date": date_str,
                "total_entries": 0,
                "work_time_minutes": 0,
                "state_distribution": {},
                "tasks": [],
                "first_activity": "",
                "last_activity": "",
            }

        entries.sort(key=lambda e: e["timestamp"])

        # Calculate work time (time spent in work states)
        work_states = {"writing", "researching", "executing", "syncing"}
        work_minutes = 0
        for i in range(len(entries) - 1):
            if entries[i].get("state") in work_states:
                delta = entries[i + 1]["timestamp"] - entries[i]["timestamp"]
                work_minutes += min(delta, 3600) / 60  # cap at 1h per segment

        # State distribution
        state_counts: dict[str, int] = {}
        for e in entries:
            st = e.get("state", "unknown")
            state_counts[st] = state_counts.get(st, 0) + 1

        # Unique tasks (messages)
        tasks = []
        for e in entries:
            msg = e.get("message", "")
            if msg and msg not in tasks:
                tasks.append(msg)

        return {
            "agent_id": agent_id,
            "date": date_str,
            "total_entries": len(entries),
            "work_time_minutes": round(work_minutes, 1),
            "state_distribution": state_counts,
            "tasks": tasks[:30],
            "first_activity": entries[0].get("datetime", ""),
            "last_activity": entries[-1].get("datetime", ""),
        }

    def generate_all_daily_summaries(self, date_str: str = "") -> list[dict]:
        """Generate daily summaries for all agents."""
        agents = self.get_all_agents()
        summaries = []
        for agent_id in agents:
            summary = self.generate_daily_summary(agent_id, date_str)
            if summary.get("total_entries", 0) > 0:
                summaries.append(summary)
        return summaries

    def auto_cleanup(self, max_age_days: int = 30) -> dict:
        """Run cleanup and return detailed results."""
        removed = self.cleanup(max_age_days)
        remaining_agents = self.get_all_agents()
        return {
            "removed_entries": removed,
            "max_age_days": max_age_days,
            "remaining_agents": remaining_agents,
            "remaining_agent_count": len(remaining_agents),
        }

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
