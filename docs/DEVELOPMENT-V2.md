# Claw Office UI v2 — Development Guide

## Architecture Overview

Claw Office UI v2 is a complete redesign focused on **OpenClaw as a central manager** coordinating multiple AI agents (Claude Code, Codex CLI, Gemini CLI) with real-time status visualization.

### Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Flask 3.0 + Flask-SocketIO | REST API + WebSocket server |
| Frontend | Vue 3 + Vite | Reactive SPA dashboard |
| Database | SQLite (WAL mode) | Persistent storage for agents, tasks, logs |
| Charts | Chart.js + vue-chartjs | History visualization |
| Real-time | Socket.IO | Instant state updates |

### Directory Structure (v2)

```
Star-Office-UI/
├── backend/
│   ├── app_v2.py           # New Flask app with Blueprints
│   ├── __init__.py
│   ├── websocket_handler.py # Socket.IO events
│   ├── models/
│   │   ├── database.py      # SQLite schema & helpers
│   │   ├── agent.py         # Agent model (CRUD, state)
│   │   └── task.py          # Task model (lifecycle)
│   ├── routes/
│   │   ├── agents.py        # /api/agents/* endpoints
│   │   ├── tasks.py         # /api/tasks/* endpoints
│   │   ├── history.py       # /api/history/* endpoints
│   │   └── scenes.py        # /api/scenes/* endpoints
│   ├── app.py               # Legacy v1 (preserved)
│   └── requirements.txt     # Updated dependencies
├── frontend-vue/            # NEW: Vue 3 SPA
│   ├── src/
│   │   ├── App.vue          # Main app with 4-tab layout
│   │   ├── main.js          # Entry point
│   │   ├── components/
│   │   │   ├── OfficeScene.vue   # SVG office visualization
│   │   │   ├── AgentPanel.vue    # Detailed agent status cards
│   │   │   ├── TaskBoard.vue     # Task management board
│   │   │   ├── HistoryPanel.vue  # History & performance reports
│   │   │   └── ScenePicker.vue   # Theme selection
│   │   ├── composables/
│   │   │   ├── useAgents.js      # Agent state management
│   │   │   ├── useTasks.js       # Task state management
│   │   │   └── useWebSocket.js   # WebSocket connection
│   │   └── i18n/
│   │       └── index.js          # zh/en/ja translations
│   ├── dist/                # Built output (served by Flask)
│   ├── package.json
│   └── vite.config.js
├── frontend/                # Legacy v1 (preserved)
├── scripts/
│   ├── ai-office-bridge-v2.py  # Enhanced bridge script
│   ├── setup-hooks.sh          # One-click hook setup
│   └── ai-office-bridge.py     # Legacy v1 bridge
├── tests/
│   ├── conftest.py          # Test fixtures
│   ├── test_agents.py       # Agent API tests (14 tests)
│   ├── test_tasks.py        # Task API tests (10 tests)
│   └── test_history.py      # History API tests (10 tests)
└── data/
    └── claw_office.db       # SQLite database (auto-created)
```

## Quick Start

```bash
# Install backend dependencies
pip install -r backend/requirements.txt

# Install frontend dependencies & build
cd frontend-vue && npm install && npm run build && cd ..

# Start the server
python3 backend/app_v2.py

# Open http://127.0.0.1:19000
```

## Development Mode

```bash
# Terminal 1: Backend
python3 backend/app_v2.py

# Terminal 2: Frontend dev server (with hot reload)
cd frontend-vue && npm run dev
# Open http://localhost:5173 (proxies API to :19000)
```

## API Reference

### Agent Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents` | List all agents |
| GET | `/api/agents/:id` | Get agent details |
| POST | `/api/agents` | Register new agent |
| POST | `/api/agents/:id/state` | Push state update |
| POST | `/api/agents/:id/leave` | Agent goes offline |
| DELETE | `/api/agents/:id` | Remove agent |
| GET | `/api/status` | Legacy: get manager status |
| POST | `/api/set_state` | Legacy: set manager state |

### Task Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/tasks` | List tasks (filter: status, assigned_to) |
| GET | `/api/tasks/:id` | Get task with subtasks |
| POST | `/api/tasks` | Create task |
| POST | `/api/tasks/:id/assign` | Assign task to agent |
| POST | `/api/tasks/:id/status` | Update task status/progress |
| GET | `/api/tasks/:id/subtasks` | Get subtasks |

### History Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/history/agents/:id/logs` | Agent activity logs |
| GET | `/api/history/agents/:id/summary` | Agent performance summary |
| GET | `/api/history/summary` | Overall summary |
| GET | `/api/history/tasks` | Task history |
| GET | `/api/history/report/:id` | Agent performance report |
| GET | `/api/history/messages` | Inter-agent messages |
| POST | `/api/history/messages` | Post message |

### Scene Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/scenes` | List all themes |
| GET | `/api/scenes/:id` | Get theme details |

### WebSocket Events

| Event | Direction | Description |
|-------|----------|-------------|
| `agent.state_changed` | Server→Client | Agent state updated |
| `agent.joined` | Server→Client | New agent connected |
| `agent.left` | Server→Client | Agent disconnected |
| `task.created` | Server→Client | New task created |
| `task.assigned` | Server→Client | Task assigned |
| `task.completed` | Server→Client | Task completed |
| `message.new` | Server→Client | New inter-agent message |

## Agent State Machine

```
States: idle, writing, researching, executing, syncing, reviewing, error

Aliases: working→writing, coding→writing, thinking→researching,
         running→executing, testing→executing, debugging→researching

State → Area mapping:
  idle       → breakroom
  writing    → desk
  researching→ desk
  executing  → desk
  syncing    → desk
  reviewing  → desk
  error      → error_corner
```

## Task Lifecycle

```
pending → assigned → in_progress → completed
                                 → failed
                   → cancelled
```

## AI Integration

### Hook-based (Claude Code / Gemini CLI)

The bridge script intercepts tool calls and maps them to office states:

```bash
# Configure automatically
bash scripts/setup-hooks.sh

# Or manually set Claude Code hooks in ~/.claude/settings.json:
{
  "hooks": {
    "PostToolUse": [{
      "type": "command",
      "command": "python3 /path/to/ai-office-bridge-v2.py claude-code hook"
    }]
  }
}
```

### Stream-based (Codex CLI)

```bash
codex exec --json "task" 2>&1 | python3 scripts/ai-office-bridge-v2.py codex --stream
```

### Manual Push

```bash
export STAR_OFFICE_URL=http://127.0.0.1:19000
python3 scripts/ai-office-bridge-v2.py manual writing "Editing code"
```

## Available Themes

1. **Modern Office** — Clean corporate workspace
2. **Konoha Village** — Naruto-inspired ninja village
3. **Pixel Classic** — Retro pixel-art office
4. **Classroom** — School classroom setting
5. **Meeting Room** — Formal meeting room
6. **Beach Resort** — Tropical vacation resort

## Testing

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_agents.py -v
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAW_OFFICE_PORT` | 19000 | Server port |
| `CLAW_OFFICE_HOST` | 0.0.0.0 | Server host |
| `CLAW_OFFICE_DEBUG` | 1 | Debug mode |
| `CLAW_OFFICE_DB` | data/claw_office.db | Database path |
| `FLASK_SECRET_KEY` | dev-secret-... | Session secret |
| `STAR_OFFICE_URL` | http://127.0.0.1:19000 | Bridge target URL |
| `STAR_OFFICE_AGENT_ID` | (auto) | Pre-registered agent ID |
| `STAR_OFFICE_VERBOSE` | 0 | Bridge debug output |
