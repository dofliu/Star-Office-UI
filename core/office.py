"""Office manager — manages multiple agents."""

from core.agent import Agent
from core import store
from core.history import HistoryLogger


class Office:
    def __init__(self, store_path: str = "office-state.json", log_dir: str = "logs"):
        self.store_path = store_path
        self.history = HistoryLogger(log_dir)
        self.agents: dict[str, Agent] = {}
        self._load()

    def _load(self) -> None:
        data = store.load(self.store_path)
        for agent_data in data.get("agents", []):
            agent = Agent.from_dict(agent_data)
            self.agents[agent.id] = agent

    def save(self) -> None:
        data = {"agents": [a.to_dict() for a in self.agents.values()]}
        store.save(data, self.store_path)

    def add_agent(self, agent_id: str, name: str, ttl: int = 300) -> Agent:
        if agent_id in self.agents:
            raise ValueError(f"Agent '{agent_id}' already exists")
        agent = Agent(agent_id, name, ttl)
        self.agents[agent_id] = agent
        self.save()
        return agent

    def remove_agent(self, agent_id: str) -> None:
        if agent_id not in self.agents:
            raise KeyError(f"Agent '{agent_id}' not found")
        del self.agents[agent_id]
        self.save()

    def get_agent(self, agent_id: str) -> Agent:
        if agent_id not in self.agents:
            raise KeyError(f"Agent '{agent_id}' not found")
        return self.agents[agent_id]

    def set_state(self, agent_id: str, state: str, message: str = "",
                  progress: int = 0) -> Agent:
        agent = self.get_agent(agent_id)
        prev_state = agent.state
        agent.set_state(state, message, progress)
        self.save()
        # Log state change
        self.history.log_state_change(
            agent_id, state, message, progress, prev_state=prev_state
        )
        return agent

    def update_profile(self, agent_id: str, display_name: str | None = None,
                       avatar: str | None = None) -> Agent:
        agent = self.get_agent(agent_id)
        if display_name is not None:
            agent.display_name = display_name
        if avatar is not None:
            agent.avatar = avatar
        self.save()
        return agent

    def check_all_ttl(self) -> list[str]:
        """Check TTL for all agents. Returns list of agent IDs that were reset."""
        reset_ids = []
        for agent in self.agents.values():
            if agent.check_ttl():
                reset_ids.append(agent.id)
        if reset_ids:
            self.save()
        return reset_ids

    def list_agents(self) -> list[Agent]:
        self.check_all_ttl()
        return list(self.agents.values())

    def summary(self) -> str:
        agents = self.list_agents()
        if not agents:
            return "Office is empty. No agents registered."
        lines = []
        lines.append(f"Office — {len(agents)} agent(s)")
        lines.append("-" * 40)
        for a in agents:
            msg = f"  {a.message}" if a.message else ""
            lines.append(f"  [{a.state:^12}] {a.name} ({a.id}){msg}")
        return "\n".join(lines)
