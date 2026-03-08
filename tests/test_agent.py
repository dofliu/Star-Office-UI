"""Tests for core.agent."""

import time
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agent import Agent, VALID_STATES


def test_initial_state():
    a = Agent("a1", "Alice")
    assert a.state == "idle"
    assert a.message == ""
    assert a.id == "a1"
    assert a.name == "Alice"


def test_set_valid_states():
    a = Agent("a1", "Alice")
    for state in VALID_STATES:
        a.set_state(state, f"doing {state}")
        assert a.state == state
        assert a.message == f"doing {state}"


def test_set_invalid_state():
    a = Agent("a1", "Alice")
    with pytest.raises(ValueError, match="Invalid state"):
        a.set_state("sleeping")


def test_ttl_resets_work_state():
    a = Agent("a1", "Alice", ttl=1)
    a.set_state("writing", "coding")
    # Simulate time passing
    a.last_updated = time.time() - 2
    changed = a.check_ttl()
    assert changed is True
    assert a.state == "idle"
    assert a.message == ""


def test_ttl_does_not_reset_idle():
    a = Agent("a1", "Alice", ttl=1)
    a.last_updated = time.time() - 2
    changed = a.check_ttl()
    assert changed is False
    assert a.state == "idle"


def test_ttl_does_not_reset_error():
    a = Agent("a1", "Alice", ttl=1)
    a.set_state("error", "bug")
    a.last_updated = time.time() - 2
    changed = a.check_ttl()
    assert changed is False
    assert a.state == "error"


def test_to_dict_and_from_dict():
    a = Agent("a1", "Alice", ttl=120)
    a.set_state("writing", "report")
    d = a.to_dict()
    b = Agent.from_dict(d)
    assert b.id == a.id
    assert b.name == a.name
    assert b.state == a.state
    assert b.message == a.message
    assert b.ttl == a.ttl
