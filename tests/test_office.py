"""Tests for core.office."""

import os
import time
import pytest
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.office import Office


@pytest.fixture
def office(tmp_path):
    """Create an Office with a temp store file."""
    store_path = str(tmp_path / "test-state.json")
    return Office(store_path)


def test_add_agent(office):
    agent = office.add_agent("a1", "Alice")
    assert agent.id == "a1"
    assert agent.name == "Alice"
    assert len(office.agents) == 1


def test_add_duplicate_raises(office):
    office.add_agent("a1", "Alice")
    with pytest.raises(ValueError, match="already exists"):
        office.add_agent("a1", "Alice2")


def test_remove_agent(office):
    office.add_agent("a1", "Alice")
    office.remove_agent("a1")
    assert len(office.agents) == 0


def test_remove_missing_raises(office):
    with pytest.raises(KeyError, match="not found"):
        office.remove_agent("nope")


def test_set_state(office):
    office.add_agent("a1", "Alice")
    agent = office.set_state("a1", "writing", "coding")
    assert agent.state == "writing"
    assert agent.message == "coding"


def test_list_agents(office):
    office.add_agent("a1", "Alice")
    office.add_agent("a2", "Bob")
    agents = office.list_agents()
    assert len(agents) == 2


def test_persistence(tmp_path):
    store_path = str(tmp_path / "test-state.json")
    o1 = Office(store_path)
    o1.add_agent("a1", "Alice")
    o1.set_state("a1", "writing", "report")

    # Load from same file
    o2 = Office(store_path)
    assert len(o2.agents) == 1
    assert o2.agents["a1"].state == "writing"
    assert o2.agents["a1"].message == "report"


def test_ttl_check(office):
    office.add_agent("a1", "Alice", ttl=1)
    office.set_state("a1", "writing", "coding")
    office.agents["a1"].last_updated = time.time() - 2
    reset_ids = office.check_all_ttl()
    assert "a1" in reset_ids
    assert office.agents["a1"].state == "idle"


def test_summary_empty(office):
    s = office.summary()
    assert "empty" in s.lower()


def test_summary_with_agents(office):
    office.add_agent("a1", "Alice")
    office.set_state("a1", "writing", "report")
    s = office.summary()
    assert "Alice" in s
    assert "writing" in s
