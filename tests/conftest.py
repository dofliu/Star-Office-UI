"""Test fixtures for Claw Office UI."""

import os
import sys
import pytest
import tempfile

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use temp database for tests
os.environ["CLAW_OFFICE_DB"] = os.path.join(tempfile.gettempdir(), "test_claw_office.db")


@pytest.fixture
def app():
    """Create test Flask app."""
    from backend.app_v2 import create_app
    app = create_app()
    app.config["TESTING"] = True
    yield app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before each test."""
    db_path = os.environ["CLAW_OFFICE_DB"]
    if os.path.exists(db_path):
        os.unlink(db_path)
    # Re-init
    from backend.models.database import init_db, _local
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None
    init_db()
    yield
    # Cleanup
    if hasattr(_local, "conn") and _local.conn:
        _local.conn.close()
        _local.conn = None
