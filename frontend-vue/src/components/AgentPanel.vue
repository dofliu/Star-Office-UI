<template>
  <div class="agent-panel">
    <div class="panel-header">
      <h2>{{ t('agents') }}</h2>
      <span class="badge">{{ onlineCount }}/{{ agents.length }}</span>
    </div>

    <div class="agent-list" v-if="agents.length > 0">
      <!-- Manager first -->
      <div v-for="agent in sortedAgents" :key="agent.id"
           class="agent-card" :class="[agent.state, agent.auth_status]">
        <div class="agent-header">
          <div class="agent-avatar" :style="{ background: avatarColor(agent) }">
            {{ agent.name?.[0] || '?' }}
          </div>
          <div class="agent-info">
            <div class="agent-name">
              {{ agent.name }}
              <span class="role-badge" :class="agent.role">{{ t(agent.role) }}</span>
            </div>
            <div class="agent-source" v-if="agent.source">{{ agent.source }}</div>
          </div>
          <div class="agent-status-indicator">
            <span class="status-dot" :class="agent.auth_status"></span>
          </div>
        </div>

        <div class="agent-state-row">
          <span class="state-label" :class="agent.state">{{ t(agent.state) }}</span>
          <span class="last-activity" v-if="agent.last_push_at">
            {{ timeAgo(agent.last_push_at) }}
          </span>
        </div>

        <!-- Detail -->
        <div class="agent-detail" v-if="agent.detail">
          <span class="detail-label">{{ t('currentlyDoing') }}:</span>
          {{ agent.detail }}
        </div>

        <!-- Current tool -->
        <div class="agent-tool" v-if="agent.current_tool">
          <code>{{ agent.current_tool }}</code>
          <span class="tool-count">({{ agent.tool_call_count || 0 }} {{ t('toolCalls') }})</span>
        </div>

        <!-- Progress bar -->
        <div class="progress-container" v-if="agent.progress > 0">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: agent.progress + '%' }" :class="agent.state"></div>
          </div>
          <span class="progress-text">{{ agent.progress }}%</span>
        </div>

        <!-- Token usage -->
        <div class="token-usage" v-if="agent.token_input > 0 || agent.token_output > 0">
          <span class="token-label">{{ t('tokenUsage') }}:</span>
          <span class="token-in">{{ formatTokens(agent.token_input) }} in</span>
          <span class="token-sep">/</span>
          <span class="token-out">{{ formatTokens(agent.token_output) }} out</span>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else>
      <p>{{ t('noAgents') }}</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  agents: { type: Array, default: () => [] },
  t: { type: Function, required: true },
})

const onlineCount = computed(() =>
  props.agents.filter(a => a.auth_status !== 'offline').length
)

const sortedAgents = computed(() => {
  return [...props.agents].sort((a, b) => {
    if (a.role === 'manager') return -1
    if (b.role === 'manager') return 1
    if (a.auth_status === 'offline' && b.auth_status !== 'offline') return 1
    if (b.auth_status === 'offline' && a.auth_status !== 'offline') return -1
    return 0
  })
})

const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']
function avatarColor(agent) {
  if (agent.role === 'manager') return '#f59e0b'
  const hash = agent.name?.split('').reduce((h, c) => h + c.charCodeAt(0), 0) || 0
  return colors[hash % colors.length]
}

function timeAgo(isoStr) {
  if (!isoStr) return ''
  const diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000)
  if (diff < 60) return props.t('secondsAgo', { n: diff })
  if (diff < 3600) return props.t('minutesAgo', { n: Math.floor(diff / 60) })
  return props.t('hoursAgo', { n: Math.floor(diff / 3600) })
}

function formatTokens(n) {
  if (!n || n === 0) return '0'
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}
</script>

<style scoped>
.agent-panel {
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

.panel-header h2 {
  font-size: 14px;
  font-weight: 600;
}

.badge {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--bg-card-hover);
  border-radius: 10px;
  color: var(--text-secondary);
}

.agent-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.agent-card {
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 12px;
  margin-bottom: 8px;
  border-left: 3px solid var(--text-muted);
  transition: all 0.2s;
}
.agent-card:hover {
  background: var(--bg-card-hover);
}
.agent-card.writing { border-left-color: #3b82f6; }
.agent-card.researching { border-left-color: #8b5cf6; }
.agent-card.executing { border-left-color: #f59e0b; }
.agent-card.syncing { border-left-color: #06b6d4; }
.agent-card.reviewing { border-left-color: #10b981; }
.agent-card.error { border-left-color: #ef4444; }
.agent-card.offline { opacity: 0.5; }

.agent-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.agent-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.agent-info { flex: 1; min-width: 0; }

.agent-name {
  font-weight: 600;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.role-badge {
  font-size: 9px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--accent);
  color: white;
  font-weight: 500;
  text-transform: uppercase;
}
.role-badge.manager { background: #f59e0b; }

.agent-source {
  font-size: 11px;
  color: var(--text-muted);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}
.status-dot.approved { background: var(--success); }
.status-dot.pending { background: var(--warning); }
.status-dot.offline { background: var(--text-muted); }

.agent-state-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.state-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.state-label.idle { color: var(--text-muted); }
.state-label.writing { color: #3b82f6; }
.state-label.researching { color: #8b5cf6; }
.state-label.executing { color: #f59e0b; }
.state-label.syncing { color: #06b6d4; }
.state-label.reviewing { color: #10b981; }
.state-label.error { color: #ef4444; }

.last-activity {
  font-size: 10px;
  color: var(--text-muted);
}

.agent-detail {
  font-size: 12px;
  color: var(--text-secondary);
  margin: 4px 0;
  line-height: 1.4;
}
.detail-label {
  color: var(--text-muted);
  font-size: 10px;
}

.agent-tool {
  font-size: 11px;
  margin: 4px 0;
  color: var(--text-secondary);
}
.agent-tool code {
  background: var(--bg-primary);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--font-mono);
  font-size: 10px;
}
.tool-count {
  color: var(--text-muted);
  font-size: 10px;
  margin-left: 4px;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}
.progress-bar {
  flex: 1;
  height: 4px;
  background: var(--bg-primary);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}
.progress-fill.writing { background: #3b82f6; }
.progress-fill.researching { background: #8b5cf6; }
.progress-fill.executing { background: #f59e0b; }
.progress-fill.syncing { background: #06b6d4; }
.progress-fill.reviewing { background: #10b981; }
.progress-text {
  font-size: 10px;
  color: var(--text-muted);
  font-family: var(--font-mono);
  width: 30px;
  text-align: right;
}

.token-usage {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 4px;
  font-family: var(--font-mono);
}
.token-label { margin-right: 4px; }
.token-in { color: #3b82f6; }
.token-out { color: #10b981; }
.token-sep { margin: 0 4px; }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-muted);
}
</style>
