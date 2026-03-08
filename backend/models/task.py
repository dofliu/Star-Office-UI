"""
Claw Office UI - Task Model

Task lifecycle: pending → assigned → in_progress → completed/failed
OpenClaw creates and assigns tasks; worker agents report progress.
"""

import uuid
from .database import get_db, row_to_dict, rows_to_list, now_iso


VALID_STATUSES = {"pending", "assigned", "in_progress", "completed", "failed", "cancelled"}
VALID_PRIORITIES = {"low", "normal", "high", "urgent"}


def create_task(title: str, created_by: str, description: str = "",
                priority: str = "normal", parent_task_id: str = None) -> dict:
    """Create a new task."""
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    now = now_iso()
    db = get_db()
    db.execute(
        """INSERT INTO tasks (id, title, description, created_by, status, priority,
           parent_task_id, created_at, updated_at)
           VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
        (task_id, title, description, created_by, priority, parent_task_id, now, now)
    )
    db.commit()
    return get_task(task_id)


def get_task(task_id: str) -> dict | None:
    """Get task by ID."""
    db = get_db()
    row = db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_dict(row)


def list_tasks(status: str = None, assigned_to: str = None,
               created_by: str = None, limit: int = 100) -> list:
    """List tasks with optional filters."""
    db = get_db()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)
    if assigned_to:
        query += " AND assigned_to = ?"
        params.append(assigned_to)
    if created_by:
        query += " AND created_by = ?"
        params.append(created_by)

    query += " ORDER BY CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END, created_at DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()
    return rows_to_list(rows)


def assign_task(task_id: str, agent_id: str) -> dict | None:
    """Assign task to an agent."""
    now = now_iso()
    db = get_db()
    db.execute(
        "UPDATE tasks SET assigned_to = ?, status = 'assigned', updated_at = ? WHERE id = ?",
        (agent_id, now, task_id)
    )
    db.commit()
    return get_task(task_id)


def update_task_status(task_id: str, status: str, progress: int = None,
                       result: str = None) -> dict | None:
    """Update task status and optionally progress/result."""
    if status not in VALID_STATUSES:
        return None

    now = now_iso()
    db = get_db()

    updates = ["status = ?", "updated_at = ?"]
    params = [status, now]

    if progress is not None:
        updates.append("progress = ?")
        params.append(progress)
    if result is not None:
        updates.append("result = ?")
        params.append(result)
    if status == "in_progress" and not get_task(task_id).get("started_at"):
        updates.append("started_at = ?")
        params.append(now)
    if status in ("completed", "failed"):
        updates.append("completed_at = ?")
        params.append(now)

    params.append(task_id)
    db.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
    db.commit()
    return get_task(task_id)


def get_subtasks(parent_task_id: str) -> list:
    """Get all subtasks of a parent task."""
    db = get_db()
    rows = db.execute(
        "SELECT * FROM tasks WHERE parent_task_id = ? ORDER BY created_at ASC",
        (parent_task_id,)
    ).fetchall()
    return rows_to_list(rows)


def get_task_tree(task_id: str) -> dict | None:
    """Get task with its subtasks."""
    task = get_task(task_id)
    if task:
        task["subtasks"] = get_subtasks(task_id)
    return task
