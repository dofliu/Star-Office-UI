"""
Claw Office UI - Task Routes

API endpoints for task management (OpenClaw task delegation system).
"""

from flask import Blueprint, request, jsonify
from ..models import task as task_model
from ..models import agent as agent_model
from ..models.database import get_db

bp = Blueprint("tasks", __name__, url_prefix="/api")


@bp.route("/tasks", methods=["GET"])
def list_tasks():
    """List tasks with optional filters."""
    status = request.args.get("status")
    assigned_to = request.args.get("assigned_to")
    created_by = request.args.get("created_by")
    limit = request.args.get("limit", 100, type=int)

    tasks = task_model.list_tasks(
        status=status, assigned_to=assigned_to,
        created_by=created_by, limit=limit
    )
    return jsonify({"tasks": tasks})


@bp.route("/tasks/<task_id>", methods=["GET"])
def get_task(task_id):
    """Get task details with subtasks."""
    task = task_model.get_task_tree(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    return jsonify(task)


@bp.route("/tasks", methods=["POST"])
def create_task():
    """Create a new task (typically by OpenClaw)."""
    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400

    created_by = data.get("createdBy", "agent_openclaw")
    description = data.get("description", "")
    priority = data.get("priority", "normal")
    parent_task_id = data.get("parentTaskId")

    # Validate creator exists
    creator = agent_model.get_agent(created_by)
    if not creator:
        return jsonify({"error": "Creator agent not found"}), 404

    task = task_model.create_task(
        title=title, created_by=created_by,
        description=description, priority=priority,
        parent_task_id=parent_task_id
    )
    return jsonify({"task": task}), 201


@bp.route("/tasks/<task_id>/assign", methods=["POST"])
def assign_task(task_id):
    """Assign task to an agent."""
    data = request.get_json(silent=True) or {}
    agent_id = data.get("agentId", "").strip()
    if not agent_id:
        return jsonify({"error": "agentId is required"}), 400

    task = task_model.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    agent = agent_model.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    updated = task_model.assign_task(task_id, agent_id)
    return jsonify({"task": updated})


@bp.route("/tasks/<task_id>/status", methods=["POST"])
def update_task_status(task_id):
    """Update task status/progress."""
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if not status:
        return jsonify({"error": "status is required"}), 400

    task = task_model.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    progress = data.get("progress")
    result = data.get("result")

    updated = task_model.update_task_status(
        task_id=task_id, status=status,
        progress=progress, result=result
    )
    if not updated:
        return jsonify({"error": f"Invalid status: {status}"}), 400
    return jsonify({"task": updated})


@bp.route("/tasks/<task_id>/subtasks", methods=["GET"])
def get_subtasks(task_id):
    """Get subtasks of a task."""
    task = task_model.get_task(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404

    subtasks = task_model.get_subtasks(task_id)
    return jsonify({"subtasks": subtasks})
