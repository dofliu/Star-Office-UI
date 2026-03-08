#!/usr/bin/env python3
"""
Claw Office UI - Backend API Server (v2)

Redesigned backend with Blueprint architecture, SQLite persistence,
WebSocket real-time updates, and OpenClaw task management system.
"""

import os
import sys

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS

from backend.models.database import init_db, close_db, get_db
from backend.models.agent import ensure_openclaw_agent
from backend.routes.agents import bp as agents_bp
from backend.routes.tasks import bp as tasks_bp
from backend.routes.history import bp as history_bp
from backend.routes.scenes import bp as scenes_bp
from backend.websocket_handler import init_websocket, socketio

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend-vue", "dist")

# Configuration
PORT = int(os.environ.get("CLAW_OFFICE_PORT", 19000))
HOST = os.environ.get("CLAW_OFFICE_HOST", "0.0.0.0")
DEBUG = os.environ.get("CLAW_OFFICE_DEBUG", "1") == "1"


def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__, static_folder=None)
    app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-prod")

    # CORS for Vue dev server
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    app.register_blueprint(agents_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(scenes_bp)

    # Initialize WebSocket
    init_websocket(app)

    # Initialize database
    with app.app_context():
        init_db()
        ensure_openclaw_agent()

    # --- Static file serving (production) ---

    @app.route("/")
    def serve_index():
        if os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
            return send_from_directory(FRONTEND_DIST, "index.html")
        return jsonify({
            "service": "Claw Office UI",
            "version": "2.0.0",
            "status": "running",
            "note": "Frontend not built. Run: cd frontend-vue && npm run build",
        })

    @app.route("/<path:path>")
    def serve_static(path):
        if os.path.exists(os.path.join(FRONTEND_DIST, path)):
            return send_from_directory(FRONTEND_DIST, path)
        # Fallback to index.html for SPA routing
        if os.path.exists(os.path.join(FRONTEND_DIST, "index.html")):
            return send_from_directory(FRONTEND_DIST, "index.html")
        return jsonify({"error": "Not found"}), 404

    # --- Health check ---

    @app.route("/health")
    @app.route("/api/health")
    def health():
        return jsonify({"status": "ok", "version": "2.0.0"})

    # --- Cleanup ---

    @app.teardown_appcontext
    def teardown(exception):
        close_db()

    return app


app = create_app()

if __name__ == "__main__":
    print(f"🏢 Claw Office UI starting on http://{HOST}:{PORT}")
    socketio.run(app, host=HOST, port=PORT, debug=DEBUG, allow_unsafe_werkzeug=True)
