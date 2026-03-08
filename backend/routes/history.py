"""
Claw Office UI - History Routes

API endpoints for work history, daily summaries, and performance reports.
"""

import json
from flask import Blueprint, request, jsonify
from ..models.database import get_db, rows_to_list, now_iso

bp = Blueprint("history", __name__, url_prefix="/api/history")


@bp.route("/agents/<agent_id>/logs", methods=["GET"])
def get_agent_logs(agent_id):
    """Get agent activity logs with time range filter.

    Query params:
        range: 1d, 7d, 30d (default 7d)
        limit: max records (default 500)
    """
    range_str = request.args.get("range", "7d")
    limit = request.args.get("limit", 500, type=int)

    days = _parse_range(range_str)
    db = get_db()
    rows = db.execute(
        """SELECT * FROM agent_logs
           WHERE agent_id = ? AND timestamp >= datetime('now', ?)
           ORDER BY timestamp DESC LIMIT ?""",
        (agent_id, f"-{days} days", limit)
    ).fetchall()
    return jsonify({"logs": rows_to_list(rows), "count": len(rows)})


@bp.route("/agents/<agent_id>/summary", methods=["GET"])
def get_agent_summary(agent_id):
    """Get agent performance summary for a time range."""
    range_str = request.args.get("range", "7d")
    days = _parse_range(range_str)
    db = get_db()

    # State distribution
    state_dist = db.execute(
        """SELECT state, COUNT(*) as count
           FROM agent_logs
           WHERE agent_id = ? AND timestamp >= datetime('now', ?)
           GROUP BY state ORDER BY count DESC""",
        (agent_id, f"-{days} days")
    ).fetchall()

    # Tool usage
    tool_dist = db.execute(
        """SELECT tool_name, COUNT(*) as count
           FROM agent_logs
           WHERE agent_id = ? AND tool_name IS NOT NULL
             AND timestamp >= datetime('now', ?)
           GROUP BY tool_name ORDER BY count DESC""",
        (agent_id, f"-{days} days")
    ).fetchall()

    # Daily activity counts
    daily_activity = db.execute(
        """SELECT DATE(timestamp) as date, COUNT(*) as activity_count
           FROM agent_logs
           WHERE agent_id = ? AND timestamp >= datetime('now', ?)
           GROUP BY DATE(timestamp) ORDER BY date ASC""",
        (agent_id, f"-{days} days")
    ).fetchall()

    # Task stats
    task_stats = db.execute(
        """SELECT status, COUNT(*) as count
           FROM tasks
           WHERE assigned_to = ? AND created_at >= datetime('now', ?)
           GROUP BY status""",
        (agent_id, f"-{days} days")
    ).fetchall()

    return jsonify({
        "agentId": agent_id,
        "range": range_str,
        "stateDistribution": rows_to_list(state_dist),
        "toolUsage": rows_to_list(tool_dist),
        "dailyActivity": rows_to_list(daily_activity),
        "taskStats": rows_to_list(task_stats),
    })


@bp.route("/summary", methods=["GET"])
def get_overall_summary():
    """Get overall summary across all agents."""
    range_str = request.args.get("range", "7d")
    days = _parse_range(range_str)
    db = get_db()

    # Per-agent summary
    agent_summaries = db.execute(
        """SELECT a.id, a.name, a.role,
                  COUNT(l.id) as total_activities,
                  SUM(CASE WHEN l.state IN ('writing','executing','researching','syncing','reviewing') THEN 1 ELSE 0 END) as work_activities
           FROM agents a
           LEFT JOIN agent_logs l ON a.id = l.agent_id AND l.timestamp >= datetime('now', ?)
           GROUP BY a.id ORDER BY total_activities DESC""",
        (f"-{days} days",)
    ).fetchall()

    # Task completion rates
    task_summary = db.execute(
        """SELECT assigned_to,
                  COUNT(*) as total,
                  SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                  SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
           FROM tasks
           WHERE created_at >= datetime('now', ?)
           GROUP BY assigned_to""",
        (f"-{days} days",)
    ).fetchall()

    return jsonify({
        "range": range_str,
        "agentSummaries": rows_to_list(agent_summaries),
        "taskSummary": rows_to_list(task_summary),
    })


@bp.route("/tasks", methods=["GET"])
def get_task_history():
    """Get completed/failed tasks history."""
    range_str = request.args.get("range", "30d")
    days = _parse_range(range_str)
    status = request.args.get("status")
    limit = request.args.get("limit", 100, type=int)
    db = get_db()

    query = """SELECT t.*, a.name as assigned_to_name, c.name as created_by_name
               FROM tasks t
               LEFT JOIN agents a ON t.assigned_to = a.id
               LEFT JOIN agents c ON t.created_by = c.id
               WHERE t.created_at >= datetime('now', ?)"""
    params = [f"-{days} days"]

    if status:
        query += " AND t.status = ?"
        params.append(status)

    query += " ORDER BY t.updated_at DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(query, params).fetchall()
    return jsonify({"tasks": rows_to_list(rows), "count": len(rows)})


@bp.route("/report/<agent_id>", methods=["GET"])
def get_agent_report(agent_id):
    """Generate performance report for an agent (考核報告).

    Returns work hours estimate, completion rate, state breakdown, etc.
    """
    range_str = request.args.get("range", "30d")
    days = _parse_range(range_str)
    db = get_db()

    # Estimate active hours (each log entry ≈ 15 seconds of work)
    log_count = db.execute(
        """SELECT COUNT(*) as cnt FROM agent_logs
           WHERE agent_id = ? AND timestamp >= datetime('now', ?)
             AND state IN ('writing','executing','researching','syncing','reviewing')""",
        (agent_id, f"-{days} days")
    ).fetchone()

    active_entries = log_count["cnt"] if log_count else 0
    estimated_hours = round(active_entries * 15 / 3600, 1)  # 15s per entry

    # Task completion
    tasks = db.execute(
        """SELECT COUNT(*) as total,
                  SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) as completed,
                  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed
           FROM tasks WHERE assigned_to = ? AND created_at >= datetime('now', ?)""",
        (agent_id, f"-{days} days")
    ).fetchone()

    total_tasks = tasks["total"] if tasks else 0
    completed = tasks["completed"] if tasks else 0
    completion_rate = round(completed / total_tasks * 100, 1) if total_tasks > 0 else 0

    # Most used tools
    top_tools = db.execute(
        """SELECT tool_name, COUNT(*) as count FROM agent_logs
           WHERE agent_id = ? AND tool_name IS NOT NULL
             AND timestamp >= datetime('now', ?)
           GROUP BY tool_name ORDER BY count DESC LIMIT 10""",
        (agent_id, f"-{days} days")
    ).fetchall()

    # Daily work pattern
    daily_pattern = db.execute(
        """SELECT DATE(timestamp) as date,
                  COUNT(*) as entries,
                  MIN(timestamp) as first_activity,
                  MAX(timestamp) as last_activity
           FROM agent_logs
           WHERE agent_id = ? AND timestamp >= datetime('now', ?)
           GROUP BY DATE(timestamp) ORDER BY date ASC""",
        (agent_id, f"-{days} days")
    ).fetchall()

    return jsonify({
        "agentId": agent_id,
        "range": range_str,
        "estimatedActiveHours": estimated_hours,
        "totalTasks": total_tasks,
        "completedTasks": completed,
        "failedTasks": tasks["failed"] if tasks else 0,
        "completionRate": completion_rate,
        "topTools": rows_to_list(top_tools),
        "dailyPattern": rows_to_list(daily_pattern),
    })


@bp.route("/messages", methods=["GET"])
def get_messages():
    """Get inter-agent messages."""
    limit = request.args.get("limit", 50, type=int)
    task_id = request.args.get("task_id")
    db = get_db()

    if task_id:
        rows = db.execute(
            """SELECT m.*, f.name as from_name, t.name as to_name
               FROM messages m
               LEFT JOIN agents f ON m.from_agent = f.id
               LEFT JOIN agents t ON m.to_agent = t.id
               WHERE m.task_id = ?
               ORDER BY m.timestamp ASC LIMIT ?""",
            (task_id, limit)
        ).fetchall()
    else:
        rows = db.execute(
            """SELECT m.*, f.name as from_name, t.name as to_name
               FROM messages m
               LEFT JOIN agents f ON m.from_agent = f.id
               LEFT JOIN agents t ON m.to_agent = t.id
               ORDER BY m.timestamp DESC LIMIT ?""",
            (limit,)
        ).fetchall()
    return jsonify({"messages": rows_to_list(rows)})


@bp.route("/messages", methods=["POST"])
def post_message():
    """Post an inter-agent message."""
    data = request.get_json(silent=True) or {}
    from_agent = data.get("fromAgent", "").strip()
    content = data.get("content", "").strip()
    if not from_agent or not content:
        return jsonify({"error": "fromAgent and content are required"}), 400

    to_agent = data.get("toAgent")
    msg_type = data.get("type", "info")
    task_id = data.get("taskId")

    db = get_db()
    db.execute(
        """INSERT INTO messages (from_agent, to_agent, content, msg_type, task_id, timestamp)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (from_agent, to_agent, content, msg_type, task_id, now_iso())
    )
    db.commit()
    return jsonify({"ok": True}), 201


def _parse_range(range_str: str) -> int:
    """Parse range string like '7d' to number of days."""
    range_str = range_str.strip().lower()
    if range_str.endswith("d"):
        try:
            return int(range_str[:-1])
        except ValueError:
            pass
    if range_str.endswith("w"):
        try:
            return int(range_str[:-1]) * 7
        except ValueError:
            pass
    if range_str.endswith("m"):
        try:
            return int(range_str[:-1]) * 30
        except ValueError:
            pass
    return 7  # default 7 days
