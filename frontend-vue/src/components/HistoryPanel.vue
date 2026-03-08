<template>
  <div class="history-panel">
    <!-- Controls -->
    <div class="history-header">
      <h2>{{ t('history') }}</h2>
      <div class="history-controls">
        <select v-model="selectedAgent" class="form-select">
          <option value="">All Agents</option>
          <option v-for="agent in agents" :key="agent.id" :value="agent.id">
            {{ agent.name }}
          </option>
        </select>
        <div class="range-btns">
          <button v-for="r in ranges" :key="r.value"
            class="range-btn" :class="{ active: range === r.value }"
            @click="range = r.value; fetchData()">
            {{ r.label }}
          </button>
        </div>
      </div>
    </div>

    <div class="history-content">
      <!-- Summary Cards -->
      <div class="summary-cards" v-if="report">
        <div class="summary-card">
          <div class="card-value">{{ report.estimatedActiveHours || 0 }}</div>
          <div class="card-label">{{ t('activeHours') }}</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ report.totalTasks || 0 }}</div>
          <div class="card-label">{{ t('tasks') }}</div>
        </div>
        <div class="summary-card">
          <div class="card-value success">{{ report.completionRate || 0 }}%</div>
          <div class="card-label">{{ t('completionRate') }}</div>
        </div>
        <div class="summary-card">
          <div class="card-value">{{ report.completedTasks || 0 }}</div>
          <div class="card-label">{{ t('completed') }}</div>
        </div>
      </div>

      <!-- Charts Row -->
      <div class="charts-row">
        <!-- Daily Activity Chart -->
        <div class="chart-container">
          <h3>{{ t('dailyActivity') }}</h3>
          <div class="bar-chart" v-if="dailyActivity.length > 0">
            <div class="bar-row" v-for="day in dailyActivity" :key="day.date">
              <span class="bar-label">{{ formatShortDate(day.date) }}</span>
              <div class="bar-track">
                <div class="bar-fill" :style="{ width: barWidth(day.activity_count || day.entries) + '%' }"></div>
              </div>
              <span class="bar-value">{{ day.activity_count || day.entries }}</span>
            </div>
          </div>
          <div v-else class="empty-chart">No data</div>
        </div>

        <!-- Top Tools -->
        <div class="chart-container">
          <h3>{{ t('topTools') }}</h3>
          <div class="tool-list" v-if="topTools.length > 0">
            <div class="tool-row" v-for="tool in topTools" :key="tool.tool_name">
              <code>{{ tool.tool_name }}</code>
              <div class="tool-bar-track">
                <div class="tool-bar-fill" :style="{ width: toolBarWidth(tool.count) + '%' }"></div>
              </div>
              <span class="tool-count">{{ tool.count }}</span>
            </div>
          </div>
          <div v-else class="empty-chart">No data</div>
        </div>
      </div>

      <!-- Agent Comparison (overall view) -->
      <div class="agent-comparison" v-if="!selectedAgent && overallSummary">
        <h3>Agent Performance</h3>
        <div class="comparison-table">
          <div class="table-header">
            <span>Agent</span>
            <span>Role</span>
            <span>Activities</span>
            <span>Work %</span>
          </div>
          <div class="table-row" v-for="agent in overallSummary.agentSummaries" :key="agent.id">
            <span class="agent-name-col">{{ agent.name }}</span>
            <span class="role-col" :class="agent.role">{{ agent.role }}</span>
            <span>{{ agent.total_activities }}</span>
            <span>{{ agent.total_activities > 0 ? Math.round(agent.work_activities / agent.total_activities * 100) : 0 }}%</span>
          </div>
        </div>
      </div>

      <!-- Recent Activity Log -->
      <div class="activity-log">
        <h3>Activity Log</h3>
        <div class="log-list" v-if="logs.length > 0">
          <div class="log-entry" v-for="log in logs.slice(0, 100)" :key="log.id">
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
            <span class="log-state" :class="log.state">{{ log.state }}</span>
            <span class="log-detail" v-if="log.detail">{{ log.detail }}</span>
            <code class="log-tool" v-if="log.tool_name">{{ log.tool_name }}</code>
          </div>
        </div>
        <div v-else class="empty-chart">No activity logs</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, computed } from 'vue'

const props = defineProps({
  agents: { type: Array, default: () => [] },
  t: { type: Function, required: true },
})

const selectedAgent = ref('')
const range = ref('7d')
const report = ref(null)
const logs = ref([])
const overallSummary = ref(null)

const ranges = [
  { label: '1D', value: '1d' },
  { label: '7D', value: '7d' },
  { label: '30D', value: '30d' },
]

const dailyActivity = computed(() => report.value?.dailyPattern || [])
const topTools = computed(() => report.value?.topTools || [])

const maxActivity = computed(() =>
  Math.max(1, ...dailyActivity.value.map(d => d.activity_count || d.entries || 0))
)
const maxToolCount = computed(() =>
  Math.max(1, ...topTools.value.map(t => t.count || 0))
)

function barWidth(count) { return (count / maxActivity.value) * 100 }
function toolBarWidth(count) { return (count / maxToolCount.value) * 100 }

async function fetchData() {
  if (selectedAgent.value) {
    // Single agent report
    try {
      const [reportRes, logsRes] = await Promise.all([
        fetch(`/api/history/report/${selectedAgent.value}?range=${range.value}`),
        fetch(`/api/history/agents/${selectedAgent.value}/logs?range=${range.value}`),
      ])
      report.value = await reportRes.json()
      const logsData = await logsRes.json()
      logs.value = logsData.logs || []
    } catch (e) {
      console.error('Failed to fetch agent history:', e)
    }
  } else {
    // Overall summary
    try {
      const res = await fetch(`/api/history/summary?range=${range.value}`)
      overallSummary.value = await res.json()
      report.value = null
      logs.value = []
    } catch (e) {
      console.error('Failed to fetch overall summary:', e)
    }
  }
}

function formatShortDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getMonth() + 1}/${d.getDate()}`
}

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

watch(selectedAgent, () => fetchData())

onMounted(() => fetchData())
</script>

<style scoped>
.history-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.history-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
  flex-shrink: 0;
}
.history-header h2 { font-size: 14px; }

.history-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.form-select {
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 6px 10px;
  color: var(--text-primary);
  font-size: 12px;
}

.range-btns {
  display: flex;
  gap: 2px;
}
.range-btn {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 11px;
  transition: all 0.2s;
}
.range-btn:first-child { border-radius: var(--radius) 0 0 var(--radius); }
.range-btn:last-child { border-radius: 0 var(--radius) var(--radius) 0; }
.range-btn.active { background: var(--accent); border-color: var(--accent); color: white; }

.history-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px 20px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.summary-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  text-align: center;
}
.card-value {
  font-size: 28px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}
.card-value.success { color: var(--success); }
.card-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
  text-transform: uppercase;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.chart-container {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
}
.chart-container h3 {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 12px;
  text-transform: uppercase;
}

.bar-chart { display: flex; flex-direction: column; gap: 6px; }
.bar-row { display: flex; align-items: center; gap: 8px; }
.bar-label { font-size: 10px; color: var(--text-muted); width: 36px; text-align: right; font-family: var(--font-mono); }
.bar-track { flex: 1; height: 12px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; }
.bar-fill { height: 100%; background: var(--accent); border-radius: 3px; transition: width 0.5s; }
.bar-value { font-size: 10px; color: var(--text-muted); width: 28px; font-family: var(--font-mono); }

.tool-list { display: flex; flex-direction: column; gap: 6px; }
.tool-row { display: flex; align-items: center; gap: 8px; }
.tool-row code {
  font-size: 10px;
  background: var(--bg-primary);
  padding: 1px 5px;
  border-radius: 3px;
  width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tool-bar-track { flex: 1; height: 10px; background: var(--bg-primary); border-radius: 3px; overflow: hidden; }
.tool-bar-fill { height: 100%; background: #8b5cf6; border-radius: 3px; }
.tool-count { font-size: 10px; color: var(--text-muted); width: 28px; font-family: var(--font-mono); }

.agent-comparison {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
  margin-bottom: 20px;
}
.agent-comparison h3 {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  text-transform: uppercase;
}

.comparison-table { font-size: 12px; }
.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--border);
  color: var(--text-muted);
  font-size: 10px;
  text-transform: uppercase;
}
.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid rgba(51,65,85,0.3);
}
.agent-name-col { font-weight: 500; }
.role-col { font-size: 10px; }
.role-col.manager { color: #f59e0b; }
.role-col.worker { color: #3b82f6; }

.activity-log {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 14px;
}
.activity-log h3 {
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 10px;
  text-transform: uppercase;
}

.log-list {
  max-height: 300px;
  overflow-y: auto;
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 3px 0;
  font-size: 11px;
  border-bottom: 1px solid rgba(51,65,85,0.2);
}

.log-time {
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 10px;
  width: 70px;
  flex-shrink: 0;
}

.log-state {
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 3px;
  font-weight: 600;
  width: 72px;
  text-align: center;
  flex-shrink: 0;
}
.log-state.writing { background: rgba(59,130,246,0.15); color: #3b82f6; }
.log-state.researching { background: rgba(139,92,246,0.15); color: #8b5cf6; }
.log-state.executing { background: rgba(245,158,11,0.15); color: #f59e0b; }
.log-state.idle { background: rgba(100,116,139,0.15); color: #64748b; }
.log-state.error { background: rgba(239,68,68,0.15); color: #ef4444; }

.log-detail {
  flex: 1;
  color: var(--text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.log-tool {
  font-size: 10px;
  background: var(--bg-primary);
  padding: 1px 5px;
  border-radius: 3px;
  flex-shrink: 0;
}

.empty-chart {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 12px;
}
</style>
