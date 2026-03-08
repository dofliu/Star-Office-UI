"""
Claw Office UI - Agent Model

Manages AI agent lifecycle: registration, state updates, querying.
"""

import uuid
from .database import get_db, row_to_dict, rows_to_list, now_iso

VALID_STATES = {"idle", "writing", "researching", "executing", "syncing", "error", "reviewing"}
VALID_ROLES = {"manager", "worker"}
VALID_AUTH = {"approved", "pending", "rejected", "offline"}

STATE_ALIASES = {
    "working": "writing",
    "coding": "writing",
    "thinking": "researching",
    "running": "executing",
    "testing": "executing",
    "debugging": "researching",
}

STATE_TO_AREA = {
    "idle": "breakroom",
    "writing": "desk",
    "researching": "desk",
    "executing": "desk",
    "syncing": "desk",
    "reviewing": "desk",
    "error": "error_corner",
}


def normalize_state(state: str) -> str:
    """Normalize state string, applying aliases."""
    state = state.lower().strip()
    return STATE_ALIASES.get(state, state)


def create_agent(name: str, role: str = "worker", source: str = None,
                 join_key: str = None, avatar: str = None) -> dict:
    """Create a new agent and return its data."""
    agent_id = f"agent_{uuid.uuid4().hex[:12]}"
    now = now_iso()
    db = get_db()
    db.execute(
        """INSERT INTO agents (id, name, role, source, join_key, avatar,
           auth_status, state, detail, last_push_at, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'approved', 'idle', '', ?, ?, ?)""",
        (agent_id, name, role, source, join_key, avatar, now, now, now)
    )
    db.commit()
    return get_agent(agent_id)


def get_agent(agent_id: str) -> dict | None:
    """Get agent by ID."""
    db = get_db()
    row = db.execute("SELECT * FROM agents WHERE id = ?", (agent_id,)).fetchone()
    return row_to_dict(row)


def get_agent_by_name(name: str) -> dict | None:
    """Get agent by name."""
    db = get_db()
    row = db.execute("SELECT * FROM agents WHERE name = ?", (name,)).fetchone()
    return row_to_dict(row)


def list_agents(include_offline: bool = True) -> list:
    """List all agents."""
    db = get_db()
    if include_offline:
        rows = db.execute("SELECT * FROM agents ORDER BY role DESC, created_at ASC").fetchall()
    else:
        rows = db.execute(
            "SELECT * FROM agents WHERE auth_status != 'offline' ORDER BY role DESC, created_at ASC"
        ).fetchall()
    return rows_to_list(rows)


def update_agent_state(agent_id: str, state: str, detail: str = "",
                       tool_name: str = None, progress: int = None,
                       token_input: int = None, token_output: int = None) -> dict | None:
    """Update agent state and log the change."""
    state = normalize_state(state)
    if state not in VALID_STATES:
        return None

    area = STATE_TO_AREA.get(state, "breakroom")
    now = now_iso()
    db = get_db()

    updates = ["state = ?", "detail = ?", "area = ?", "last_push_at = ?", "updated_at = ?"]
    params = [state, detail, area, now, now]

    if tool_name:
        updates.append("current_tool = ?")
        params.append(tool_name)
        updates.append("tool_call_count = tool_call_count + 1")

    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)

    if token_input is not None:
        updates.append("token_input = token_input + ?")
        params.append(token_input)

    if token_output is not None:
        updates.append("token_output = token_output + ?")
        params.append(token_output)

    params.append(agent_id)
    db.execute(f"UPDATE agents SET {', '.join(updates)} WHERE id = ?", params)

    # Log state change
    from .database import get_db as _get_db
    db.execute(
        """INSERT INTO agent_logs (agent_id, state, detail, tool_name, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (agent_id, state, detail, tool_name, now)
    )
    db.commit()
    return get_agent(agent_id)


def set_agent_offline(agent_id: str):
    """Mark agent as offline."""
    db = get_db()
    now = now_iso()
    db.execute(
        "UPDATE agents SET auth_status = 'offline', state = 'idle', area = 'breakroom', updated_at = ? WHERE id = ?",
        (now, agent_id)
    )
    db.commit()


def set_agent_online(agent_id: str):
    """Mark agent as approved/online."""
    db = get_db()
    now = now_iso()
    db.execute(
        "UPDATE agents SET auth_status = 'approved', updated_at = ? WHERE id = ?",
        (now, agent_id)
    )
    db.commit()


def delete_agent(agent_id: str):
    """Remove agent."""
    db = get_db()
    db.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
    db.commit()


def ensure_openclaw_agent() -> dict:
    """Ensure the OpenClaw manager agent exists."""
    agent = get_agent_by_name("OpenClaw")
    if not agent:
        agent_id = "agent_openclaw"
        now = now_iso()
        db = get_db()
        db.execute(
            """INSERT OR IGNORE INTO agents
               (id, name, role, source, auth_status, state, detail, created_at, updated_at)
               VALUES (?, 'OpenClaw', 'manager', 'openclaw', 'approved', 'idle', '', ?, ?)""",
            (agent_id, now, now)
        )
        db.commit()
        agent = get_agent(agent_id)
    return agent
