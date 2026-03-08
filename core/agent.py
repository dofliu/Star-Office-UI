"""Agent model with state machine."""

import time

VALID_STATES = {"idle", "writing", "researching", "executing", "syncing", "error"}
WORK_STATES = {"writing", "researching", "executing", "syncing"}
DEFAULT_TTL = 300  # seconds


DEFAULT_AVATARS = [
    "char_blue", "char_green", "char_red", "char_purple",
    "char_orange", "char_cyan", "char_pink", "char_yellow",
]


class Agent:
    def __init__(self, agent_id: str, name: str, ttl: int = DEFAULT_TTL):
        self.id = agent_id
        self.name = name
        self.display_name = ""   # custom nickname, falls back to name
        self.avatar = ""         # avatar key or image path
        self.state = "idle"
        self.message = ""
        self.progress = 0        # 0-100 progress percentage
        self.ttl = ttl
        self.last_updated = time.time()
        self.created_at = time.time()

    @property
    def label(self) -> str:
        """Display name shown in UI — uses display_name if set, else name."""
        return self.display_name or self.name

    def set_state(self, state: str, message: str = "", progress: int = 0) -> None:
        if state not in VALID_STATES:
            raise ValueError(f"Invalid state '{state}'. Must be one of: {sorted(VALID_STATES)}")
        self.state = state
        self.message = message
        self.progress = max(0, min(100, progress))
        self.last_updated = time.time()

    def check_ttl(self) -> bool:
        """If agent is in a work state and TTL expired, revert to idle.
        Returns True if state was changed."""
        if self.state in WORK_STATES:
            elapsed = time.time() - self.last_updated
            if elapsed >= self.ttl:
                self.state = "idle"
                self.message = ""
                self.progress = 0
                self.last_updated = time.time()
                return True
        return False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "label": self.label,
            "avatar": self.avatar,
            "state": self.state,
            "message": self.message,
            "progress": self.progress,
            "ttl": self.ttl,
            "last_updated": self.last_updated,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Agent":
        agent = cls(data["id"], data["name"], data.get("ttl", DEFAULT_TTL))
        agent.display_name = data.get("display_name", "")
        agent.avatar = data.get("avatar", "")
        agent.state = data.get("state", "idle")
        agent.message = data.get("message", "")
        agent.progress = data.get("progress", 0)
        agent.last_updated = data.get("last_updated", time.time())
        agent.created_at = data.get("created_at", time.time())
        return agent

    def __repr__(self) -> str:
        return f"Agent({self.id!r}, name={self.name!r}, state={self.state!r})"
