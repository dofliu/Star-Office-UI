<template>
  <div class="task-board">
    <div class="panel-header">
      <h2>{{ t('tasks') }}</h2>
      <button class="create-btn" @click="showCreate = !showCreate">+ {{ t('createTask') }}</button>
    </div>

    <!-- Create Task Form -->
    <div class="create-form" v-if="showCreate">
      <input v-model="newTask.title" :placeholder="t('taskTitle')" class="form-input" />
      <textarea v-model="newTask.description" :placeholder="t('description')" class="form-textarea" rows="2"></textarea>
      <div class="form-row">
        <select v-model="newTask.priority" class="form-select">
          <option value="low">Low</option>
          <option value="normal">Normal</option>
          <option value="high">High</option>
          <option value="urgent">Urgent</option>
        </select>
        <select v-model="newTask.assignedTo" class="form-select">
          <option value="">{{ t('assignTo') }}...</option>
          <option v-for="agent in workerAgents" :key="agent.id" :value="agent.id">
            {{ agent.name }}
          </option>
        </select>
      </div>
      <div class="form-actions">
        <button class="btn btn-primary" @click="handleCreate">{{ t('submit') }}</button>
        <button class="btn btn-secondary" @click="showCreate = false">{{ t('cancel') }}</button>
      </div>
    </div>

    <!-- Task Columns -->
    <div class="task-columns">
      <!-- Active Tasks -->
      <div class="task-column">
        <div class="column-header">
          <span class="column-title">{{ t('in_progress') }}</span>
          <span class="column-count">{{ activeTasks.length }}</span>
        </div>
        <div class="task-list">
          <div v-for="task in activeTasks" :key="task.id" class="task-card" :class="task.priority">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <span class="task-status" :class="task.status">{{ t(task.status) }}</span>
              <span class="task-priority" :class="task.priority">{{ task.priority }}</span>
            </div>
            <div class="task-assigned" v-if="task.assigned_to">
              {{ t('assignTo') }}: {{ getAgentName(task.assigned_to) }}
            </div>
            <div class="task-progress" v-if="task.progress > 0">
              <div class="mini-progress">
                <div class="mini-fill" :style="{ width: task.progress + '%' }"></div>
              </div>
              <span>{{ task.progress }}%</span>
            </div>
            <div class="task-description" v-if="task.description">{{ task.description }}</div>
          </div>
          <div v-if="activeTasks.length === 0" class="empty-col">{{ t('noTasks') }}</div>
        </div>
      </div>

      <!-- Completed Tasks -->
      <div class="task-column">
        <div class="column-header">
          <span class="column-title">{{ t('completed') }}</span>
          <span class="column-count">{{ completedTasks.length }}</span>
        </div>
        <div class="task-list">
          <div v-for="task in completedTasks.slice(0, 20)" :key="task.id" class="task-card completed">
            <div class="task-title">{{ task.title }}</div>
            <div class="task-meta">
              <span class="task-status completed">{{ t('completed') }}</span>
              <span class="task-time" v-if="task.completed_at">{{ formatDate(task.completed_at) }}</span>
            </div>
            <div class="task-assigned" v-if="task.assigned_to">
              {{ getAgentName(task.assigned_to) }}
            </div>
          </div>
          <div v-if="completedTasks.length === 0" class="empty-col">-</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'

const props = defineProps({
  tasks: { type: Array, default: () => [] },
  agents: { type: Array, default: () => [] },
  t: { type: Function, required: true },
})

const emit = defineEmits(['refresh'])

const showCreate = ref(false)
const newTask = reactive({
  title: '',
  description: '',
  priority: 'normal',
  assignedTo: '',
})

const workerAgents = computed(() =>
  props.agents.filter(a => a.role === 'worker' && a.auth_status !== 'offline')
)

const activeTasks = computed(() =>
  props.tasks.filter(t => ['pending', 'assigned', 'in_progress'].includes(t.status))
)

const completedTasks = computed(() =>
  props.tasks.filter(t => ['completed', 'failed'].includes(t.status))
)

function getAgentName(agentId) {
  const agent = props.agents.find(a => a.id === agentId)
  return agent?.name || agentId
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString()
}

async function handleCreate() {
  if (!newTask.title.trim()) return

  const body = {
    title: newTask.title,
    description: newTask.description,
    priority: newTask.priority,
    createdBy: 'agent_openclaw',
  }

  try {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    const data = await res.json()

    // If assigned, also assign
    if (newTask.assignedTo && data.task) {
      await fetch(`/api/tasks/${data.task.id}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agentId: newTask.assignedTo }),
      })
    }

    newTask.title = ''
    newTask.description = ''
    newTask.priority = 'normal'
    newTask.assignedTo = ''
    showCreate.value = false
    emit('refresh')
  } catch (e) {
    console.error('Failed to create task:', e)
  }
}
</script>

<style scoped>
.task-board {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
}
.panel-header h2 { font-size: 14px; font-weight: 600; }

.create-btn {
  padding: 4px 12px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}
.create-btn:hover { background: var(--accent-hover); }

.create-form {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-input, .form-textarea, .form-select {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 8px 10px;
  color: var(--text-primary);
  font-size: 13px;
}
.form-input:focus, .form-textarea:focus, .form-select:focus {
  outline: none;
  border-color: var(--accent);
}
.form-textarea { resize: vertical; min-height: 40px; }
.form-row { display: flex; gap: 8px; }
.form-select { flex: 1; }

.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.btn {
  padding: 6px 14px;
  border: none;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 12px;
}
.btn-primary { background: var(--accent); color: white; }
.btn-primary:hover { background: var(--accent-hover); }
.btn-secondary { background: var(--bg-card-hover); color: var(--text-secondary); }

.task-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1px;
  background: var(--border);
  flex: 1;
  overflow: hidden;
}

.task-column {
  background: var(--bg-secondary);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
}
.column-title { font-size: 12px; font-weight: 600; color: var(--text-secondary); }
.column-count {
  font-size: 10px;
  padding: 1px 6px;
  background: var(--bg-card-hover);
  border-radius: 8px;
  color: var(--text-muted);
}

.task-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.task-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 10px;
  margin-bottom: 6px;
  border-left: 3px solid var(--text-muted);
  font-size: 12px;
}
.task-card.urgent { border-left-color: #ef4444; }
.task-card.high { border-left-color: #f59e0b; }
.task-card.normal { border-left-color: #3b82f6; }
.task-card.low { border-left-color: #64748b; }
.task-card.completed { border-left-color: var(--success); opacity: 0.7; }

.task-title { font-weight: 600; margin-bottom: 4px; }

.task-meta {
  display: flex;
  gap: 6px;
  margin-bottom: 4px;
}

.task-status {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  background: var(--bg-card-hover);
  color: var(--text-secondary);
}
.task-status.completed { background: rgba(34,197,94,0.15); color: var(--success); }
.task-status.in_progress { background: rgba(59,130,246,0.15); color: var(--accent); }
.task-status.failed { background: rgba(239,68,68,0.15); color: var(--error); }

.task-priority {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
}
.task-priority.urgent { background: rgba(239,68,68,0.15); color: #ef4444; }
.task-priority.high { background: rgba(245,158,11,0.15); color: #f59e0b; }

.task-assigned {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.task-description {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  line-height: 1.4;
}

.task-progress {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 10px;
  color: var(--text-muted);
}
.mini-progress {
  flex: 1;
  height: 3px;
  background: var(--bg-primary);
  border-radius: 2px;
  overflow: hidden;
}
.mini-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 2px;
}

.task-time { font-size: 10px; color: var(--text-muted); }

.empty-col {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
