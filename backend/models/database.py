"""
Claw Office UI - SQLite Database Layer

Manages all persistent storage: agents, tasks, history logs, daily summaries.
"""

import sqlite3
import os
import threading
import json
from datetime import datetime, timezone

DB_PATH = os.environ.get("CLAW_OFFICE_DB", os.path.join(os.path.dirname(__file__), "..", "..", "data", "claw_office.db"))

_local = threading.local()


def get_db() -> sqlite3.Connection:
    """Get thread-local database connection."""
    if not hasattr(_local, "conn") or _local.conn is None:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        _local.conn = sqlite3.connect(DB_PATH)
        _local.conn.row_factory = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn


def close_db():
    """Close thread-local database connection."""
    if hasattr(_local, "conn") and _local.conn is not None:
        _local.conn.close()
        _local.conn = None


def init_db():
    """Initialize database schema."""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS agents (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'worker',
            avatar TEXT DEFAULT NULL,
            source TEXT DEFAULT NULL,
            join_key TEXT DEFAULT NULL,
            auth_status TEXT NOT NULL DEFAULT 'approved',
            state TEXT NOT NULL DEFAULT 'idle',
            detail TEXT DEFAULT '',
            progress INTEGER DEFAULT 0,
            area TEXT DEFAULT 'breakroom',
            current_tool TEXT DEFAULT NULL,
            tool_call_count INTEGER DEFAULT 0,
            token_input INTEGER DEFAULT 0,
            token_output INTEGER DEFAULT 0,
            last_push_at TEXT DEFAULT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_by TEXT NOT NULL,
            assigned_to TEXT DEFAULT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            priority TEXT NOT NULL DEFAULT 'normal',
            progress INTEGER DEFAULT 0,
            result TEXT DEFAULT NULL,
            parent_task_id TEXT DEFAULT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            started_at TEXT DEFAULT NULL,
            completed_at TEXT DEFAULT NULL,
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES agents(id),
            FOREIGN KEY (assigned_to) REFERENCES agents(id),
            FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
        );

        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            state TEXT NOT NULL,
            detail TEXT DEFAULT '',
            tool_name TEXT DEFAULT NULL,
            task_id TEXT DEFAULT NULL,
            metadata TEXT DEFAULT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        );

        CREATE TABLE IF NOT EXISTS daily_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            agent_id TEXT NOT NULL,
            total_tasks INTEGER DEFAULT 0,
            completed_tasks INTEGER DEFAULT 0,
            total_time_seconds INTEGER DEFAULT 0,
            states_breakdown TEXT DEFAULT '{}',
            tools_breakdown TEXT DEFAULT '{}',
            summary TEXT DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(date, agent_id),
            FOREIGN KEY (agent_id) REFERENCES agents(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_agent TEXT NOT NULL,
            to_agent TEXT DEFAULT NULL,
            content TEXT NOT NULL,
            msg_type TEXT NOT NULL DEFAULT 'info',
            task_id TEXT DEFAULT NULL,
            timestamp TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (from_agent) REFERENCES agents(id),
            FOREIGN KEY (task_id) REFERENCES tasks(id)
        );

        CREATE INDEX IF NOT EXISTS idx_agent_logs_agent_id ON agent_logs(agent_id);
        CREATE INDEX IF NOT EXISTS idx_agent_logs_timestamp ON agent_logs(timestamp);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
        CREATE INDEX IF NOT EXISTS idx_daily_summaries_date ON daily_summaries(date);
        CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
    """)
    db.commit()


def row_to_dict(row):
    """Convert sqlite3.Row to dict."""
    if row is None:
        return None
    return dict(row)


def rows_to_list(rows):
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(r) for r in rows]


def now_iso():
    """Return current UTC time in ISO format."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
