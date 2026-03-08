#!/usr/bin/env python3
"""Star Office API Server — Flask REST API on port 19200."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, send_from_directory
from core.office import Office
from core.agent import VALID_STATES, DEFAULT_AVATARS

PORT = int(os.environ.get("STAR_OFFICE_PORT", 19200))
STORE_PATH = os.environ.get("STAR_OFFICE_STORE", "office-state.json")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend-v2")

app = Flask(__name__, static_folder=FRONTEND_DIR)


def get_office():
    return Office(STORE_PATH)


# --- Health ---

@app.route("/health")
def health():
    return jsonify({"status": "ok", "port": PORT})


# --- Agents ---

@app.route("/agents", methods=["GET"])
def list_agents():
    office = get_office()
    agents = office.list_agents()
    return jsonify({"agents": [a.to_dict() for a in agents]})


@app.route("/agents/<agent_id>", methods=["GET"])
def get_agent(agent_id):
    office = get_office()
    try:
        agent = office.get_agent(agent_id)
        agent.check_ttl()
        return jsonify(agent.to_dict())
    except KeyError:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404


@app.route("/agents", methods=["POST"])
def add_agent():
    data = request.get_json(silent=True) or {}
    agent_id = data.get("id")
    name = data.get("name")
    ttl = data.get("ttl", 300)

    display_name = data.get("display_name", "")
    avatar = data.get("avatar", "")

    if not agent_id or not name:
        return jsonify({"error": "Missing 'id' and 'name'"}), 400

    office = get_office()
    try:
        agent = office.add_agent(agent_id, name, ttl)
        if display_name or avatar:
            office.update_profile(agent_id, display_name or None, avatar or None)
            agent = office.get_agent(agent_id)
        return jsonify(agent.to_dict()), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409


@app.route("/agents/<agent_id>", methods=["DELETE"])
def remove_agent(agent_id):
    office = get_office()
    try:
        office.remove_agent(agent_id)
        return jsonify({"removed": agent_id})
    except KeyError:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404


# --- Profile (display_name, avatar) ---

@app.route("/agents/<agent_id>/profile", methods=["POST"])
def update_profile(agent_id):
    data = request.get_json(silent=True) or {}
    display_name = data.get("display_name")
    avatar = data.get("avatar")

    if display_name is None and avatar is None:
        return jsonify({"error": "Provide 'display_name' and/or 'avatar'"}), 400

    office = get_office()
    try:
        agent = office.update_profile(agent_id, display_name, avatar)
        return jsonify(agent.to_dict())
    except KeyError:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404


@app.route("/avatars", methods=["GET"])
def list_avatars():
    return jsonify({"avatars": DEFAULT_AVATARS})


# --- State ---

@app.route("/agents/<agent_id>/state", methods=["POST"])
def set_state(agent_id):
    data = request.get_json(silent=True) or {}
    state = data.get("state")
    message = data.get("message", "")
    progress = data.get("progress", 0)

    if not state:
        return jsonify({"error": "Missing 'state'"}), 400

    office = get_office()
    try:
        agent = office.set_state(agent_id, state, message, progress)
        return jsonify(agent.to_dict())
    except KeyError:
        return jsonify({"error": f"Agent '{agent_id}' not found"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# --- Frontend ---

@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/ui/<path:filename>")
def serve_frontend(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# --- API overview ---

@app.route("/api/status")
def api_status():
    office = get_office()
    agents = office.list_agents()
    return jsonify({
        "service": "Star Office",
        "port": PORT,
        "agent_count": len(agents),
        "agents": [
            {"id": a.id, "name": a.name, "label": a.label, "avatar": a.avatar,
             "state": a.state, "message": a.message}
            for a in agents
        ],
        "valid_states": sorted(VALID_STATES),
    })


if __name__ == "__main__":
    print(f"Star Office API starting on port {PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=True)
