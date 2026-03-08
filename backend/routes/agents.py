"""
Claw Office UI - Agent Routes

API endpoints for agent management and state updates.
"""

from flask import Blueprint, request, jsonify
from ..models import agent as agent_model
from ..models.database import get_db, now_iso

bp = Blueprint("agents", __name__, url_prefix="/api")


@bp.route("/agents", methods=["GET"])
def list_agents():
    """List all agents with their current status."""
    include_offline = request.args.get("include_offline", "true").lower() == "true"
    agents = agent_model.list_agents(include_offline=include_offline)
    return jsonify({"agents": agents})


@bp.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    """Get single agent details."""
    agent = agent_model.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    return jsonify(agent)


@bp.route("/agents", methods=["POST"])
def register_agent():
    """Register a new agent (join the office)."""
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400

    role = data.get("role", "worker")
    if role not in agent_model.VALID_ROLES:
        role = "worker"

    source = data.get("source")
    join_key = data.get("joinKey")
    avatar = data.get("avatar")

    # Check if agent with same name already exists
    existing = agent_model.get_agent_by_name(name)
    if existing:
        # Re-activate existing agent
        agent_model.set_agent_online(existing["id"])
        return jsonify({"agent": agent_model.get_agent(existing["id"]), "rejoined": True})

    agent = agent_model.create_agent(
        name=name, role=role, source=source,
        join_key=join_key, avatar=avatar
    )
    return jsonify({"agent": agent, "rejoined": False}), 201


@bp.route("/agents/<agent_id>/state", methods=["POST"])
def push_state(agent_id):
    """Push agent state update."""
    agent = agent_model.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    data = request.get_json(silent=True) or {}
    state = data.get("state", "idle")
    detail = data.get("detail", "")
    tool_name = data.get("toolName")
    progress = data.get("progress")
    token_input = data.get("tokenInput")
    token_output = data.get("tokenOutput")

    # Auto re-activate offline agents
    if agent["auth_status"] == "offline":
        agent_model.set_agent_online(agent_id)

    updated = agent_model.update_agent_state(
        agent_id=agent_id,
        state=state,
        detail=detail,
        tool_name=tool_name,
        progress=progress,
        token_input=token_input,
        token_output=token_output,
    )
    if not updated:
        return jsonify({"error": f"Invalid state: {state}"}), 400

    return jsonify({"agent": updated})


@bp.route("/agents/<agent_id>/leave", methods=["POST"])
def leave_office(agent_id):
    """Agent leaves the office."""
    agent = agent_model.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404

    agent_model.set_agent_offline(agent_id)
    return jsonify({"ok": True})


@bp.route("/agents/<agent_id>", methods=["DELETE"])
def remove_agent(agent_id):
    """Remove agent permanently."""
    agent = agent_model.get_agent(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    if agent["role"] == "manager":
        return jsonify({"error": "Cannot remove manager agent"}), 403

    agent_model.delete_agent(agent_id)
    return jsonify({"ok": True})


# --- Legacy compatibility endpoints ---

@bp.route("/status", methods=["GET"])
def get_status():
    """Get OpenClaw (manager) status - legacy compatibility."""
    agent = agent_model.ensure_openclaw_agent()
    return jsonify({
        "state": agent["state"],
        "detail": agent["detail"],
        "progress": agent["progress"],
        "updated_at": agent["updated_at"],
    })


@bp.route("/set_state", methods=["POST"])
def set_state():
    """Set OpenClaw state - legacy compatibility."""
    data = request.get_json(silent=True) or {}
    agent = agent_model.ensure_openclaw_agent()
    state = data.get("state", "idle")
    detail = data.get("detail", "")

    updated = agent_model.update_agent_state(
        agent_id=agent["id"], state=state, detail=detail
    )
    if not updated:
        return jsonify({"error": "Invalid state"}), 400
    return jsonify({"ok": True, "state": updated["state"]})
