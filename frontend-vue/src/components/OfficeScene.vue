<template>
  <div class="office-scene" ref="sceneContainer">
    <svg :viewBox="`0 0 ${width} ${height}`" class="scene-svg" xmlns="http://www.w3.org/2000/svg">
      <!-- Background based on theme -->
      <rect width="100%" height="100%" :fill="themeBg.floor" />

      <!-- Room structure -->
      <rect x="20" y="20" :width="width-40" :height="height-40" :fill="themeBg.wall" rx="8" />
      <rect x="20" :y="height * 0.65" :width="width-40" :height="height * 0.35 - 20" :fill="themeBg.floor" rx="0" />

      <!-- Grid lines (subtle) -->
      <line v-for="i in 5" :key="'vl'+i"
        :x1="width * i / 6" y1="20" :x2="width * i / 6" :y2="height - 20"
        stroke="rgba(255,255,255,0.03)" stroke-width="1" />

      <!-- Manager desk area -->
      <g :transform="`translate(${managerPos.x}, ${managerPos.y})`">
        <!-- Desk -->
        <rect x="-60" y="20" width="120" height="40" :fill="themeBg.desk" rx="4" />
        <rect x="-50" y="15" width="100" height="8" fill="#475569" rx="2" />
        <!-- Monitor -->
        <rect x="-25" y="-10" width="50" height="30" fill="#1e293b" rx="3" stroke="#475569" stroke-width="1.5" />
        <rect x="-20" y="-5" width="40" height="20" fill="#0f172a" rx="1" />
        <!-- Monitor glow when working -->
        <rect v-if="managerAgent && managerAgent.state !== 'idle'" x="-20" y="-5" width="40" height="20"
          :fill="stateColor(managerAgent.state)" opacity="0.15" rx="1">
          <animate attributeName="opacity" values="0.1;0.2;0.1" dur="2s" repeatCount="indefinite" />
        </rect>
        <!-- Label -->
        <text x="0" y="-25" text-anchor="middle" fill="#fbbf24" font-size="11" font-weight="bold">
          {{ managerAgent?.name || 'OpenClaw' }}
        </text>
        <text x="0" y="-14" text-anchor="middle" :fill="stateColor(managerAgent?.state)" font-size="9">
          {{ managerAgent?.state || 'idle' }}
        </text>
      </g>

      <!-- Worker desks -->
      <g v-for="(pos, idx) in workerPositions" :key="'desk-'+idx"
         :transform="`translate(${pos.x}, ${pos.y})`">
        <!-- Desk -->
        <rect x="-50" y="20" width="100" height="35" :fill="themeBg.desk" rx="3" opacity="0.8" />
        <rect x="-42" y="15" width="84" height="7" fill="#475569" rx="2" />
        <!-- Monitor -->
        <rect x="-20" y="-8" width="40" height="25" fill="#1e293b" rx="2" stroke="#475569" stroke-width="1" />

        <!-- Agent on this desk -->
        <template v-if="workerAgents[idx]">
          <rect x="-20" y="-8" width="40" height="25"
            :fill="stateColor(workerAgents[idx].state)" opacity="0.12" rx="2">
            <animate attributeName="opacity" values="0.08;0.18;0.08" dur="2.5s" repeatCount="indefinite" />
          </rect>
          <!-- Agent avatar circle -->
          <circle cx="0" cy="-30" r="14" :fill="agentColor(idx)" opacity="0.9" />
          <text x="0" y="-26" text-anchor="middle" fill="white" font-size="12" font-weight="bold">
            {{ workerAgents[idx].name?.[0] || '?' }}
          </text>
          <!-- Name -->
          <text x="0" y="-48" text-anchor="middle" fill="#e2e8f0" font-size="9" font-weight="500">
            {{ truncate(workerAgents[idx].name, 12) }}
          </text>
          <!-- State -->
          <text x="0" y="52" text-anchor="middle" :fill="stateColor(workerAgents[idx].state)" font-size="8">
            {{ workerAgents[idx].state }}
          </text>
          <!-- Detail (truncated) -->
          <text x="0" y="62" text-anchor="middle" fill="#64748b" font-size="7">
            {{ truncate(workerAgents[idx].detail, 20) }}
          </text>
          <!-- Progress bar -->
          <rect v-if="workerAgents[idx].progress > 0" x="-30" y="66" width="60" height="3" fill="#1e293b" rx="1.5" />
          <rect v-if="workerAgents[idx].progress > 0" x="-30" y="66"
            :width="60 * workerAgents[idx].progress / 100" height="3" :fill="stateColor(workerAgents[idx].state)" rx="1.5" />
        </template>
        <template v-else>
          <!-- Empty desk -->
          <text x="0" y="-20" text-anchor="middle" fill="#334155" font-size="9">- empty -</text>
        </template>
      </g>

      <!-- Break room area -->
      <g :transform="`translate(${breakroomPos.x}, ${breakroomPos.y})`">
        <rect x="-50" y="-20" width="100" height="60" fill="#1e293b" rx="8" stroke="#334155" stroke-width="1" />
        <text x="0" y="-30" text-anchor="middle" fill="#475569" font-size="9">Break Room</text>
        <!-- Idle agents shown here -->
        <circle v-for="(agent, i) in idleAgents.slice(0, 4)" :key="'idle-'+agent.id"
          :cx="-30 + i * 20" cy="5" r="10" :fill="agentColor(i + 10)" opacity="0.6" />
        <text v-for="(agent, i) in idleAgents.slice(0, 4)" :key="'idle-n-'+agent.id"
          :x="-30 + i * 20" y="9" text-anchor="middle" fill="white" font-size="8" font-weight="bold">
          {{ agent.name?.[0] || '?' }}
        </text>
        <text v-if="idleAgents.length > 4" x="40" y="9" fill="#64748b" font-size="8">+{{ idleAgents.length - 4 }}</text>
      </g>

      <!-- Error corner -->
      <g :transform="`translate(${errorPos.x}, ${errorPos.y})`">
        <rect x="-35" y="-20" width="70" height="40" fill="#1e293b" rx="4" stroke="#ef4444" stroke-width="1" opacity="0.5" />
        <text x="0" y="-25" text-anchor="middle" fill="#ef4444" font-size="9">Error</text>
        <circle v-for="(agent, i) in errorAgents.slice(0, 3)" :key="'err-'+agent.id"
          :cx="-15 + i * 15" cy="0" r="8" fill="#ef4444" opacity="0.5" />
      </g>

      <!-- Theme label -->
      <text :x="width / 2" :y="height - 8" text-anchor="middle" fill="#334155" font-size="10">
        {{ currentThemeData?.name?.[locale] || theme }}
      </text>
    </svg>

    <!-- Floating detail tooltips -->
    <div v-if="hoveredAgent" class="agent-tooltip" :style="tooltipStyle">
      <div class="tooltip-header">
        <span class="tooltip-name">{{ hoveredAgent.name }}</span>
        <span class="tooltip-role" :class="hoveredAgent.role">{{ hoveredAgent.role }}</span>
      </div>
      <div class="tooltip-body">
        <div>State: <strong :style="{ color: stateColor(hoveredAgent.state) }">{{ hoveredAgent.state }}</strong></div>
        <div v-if="hoveredAgent.detail">Detail: {{ hoveredAgent.detail }}</div>
        <div v-if="hoveredAgent.current_tool">Tool: {{ hoveredAgent.current_tool }}</div>
        <div>Tool calls: {{ hoveredAgent.tool_call_count || 0 }}</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useI18n } from '../i18n/index.js'

const props = defineProps({
  agents: { type: Array, default: () => [] },
  theme: { type: String, default: 'modern-office' },
  themes: { type: Array, default: () => [] },
})

const emit = defineEmits(['switch-theme'])
const { locale } = useI18n()

const width = 1280
const height = 720
const hoveredAgent = ref(null)
const tooltipStyle = ref({})

const currentThemeData = computed(() =>
  props.themes.find(t => t.id === props.theme)
)

const themeColors = {
  'modern-office': { wall: '#1a2332', floor: '#0f1a2b', desk: '#2d3748' },
  'konoha-village': { wall: '#2d1f0e', floor: '#1a1408', desk: '#4a3520' },
  'pixel-classic': { wall: '#1e293b', floor: '#0f172a', desk: '#334155' },
  'classroom': { wall: '#f5f0e1', floor: '#d4c5a0', desk: '#8b7355' },
  'meeting-room': { wall: '#1c2433', floor: '#121a27', desk: '#3a4555' },
  'resort': { wall: '#0e4a6e', floor: '#0c3d5c', desk: '#7c6c4f' },
}

const themeBg = computed(() => themeColors[props.theme] || themeColors['modern-office'])

const positions = computed(() => {
  const td = currentThemeData.value?.positions
  return {
    manager: td?.manager || { x: 200, y: 300 },
    workers: td?.workers || [
      { x: 450, y: 250 }, { x: 650, y: 250 }, { x: 850, y: 250 },
      { x: 450, y: 450 }, { x: 650, y: 450 }, { x: 850, y: 450 },
    ],
    breakroom: td?.breakroom || { x: 1100, y: 200 },
    error_corner: td?.error_corner || { x: 100, y: 600 },
  }
})

const managerPos = computed(() => positions.value.manager)
const workerPositions = computed(() => positions.value.workers)
const breakroomPos = computed(() => positions.value.breakroom)
const errorPos = computed(() => positions.value.error_corner)

const managerAgent = computed(() => props.agents.find(a => a.role === 'manager'))

const workerAgents = computed(() => {
  const working = props.agents.filter(a =>
    a.role === 'worker' && a.auth_status !== 'offline' &&
    !['idle', 'error'].includes(a.state)
  )
  const result = []
  for (let i = 0; i < workerPositions.value.length; i++) {
    result.push(working[i] || null)
  }
  return result
})

const idleAgents = computed(() =>
  props.agents.filter(a => a.state === 'idle' && a.auth_status !== 'offline' && a.role !== 'manager')
)

const errorAgents = computed(() =>
  props.agents.filter(a => a.state === 'error')
)

const agentColors = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
]

function agentColor(idx) {
  return agentColors[idx % agentColors.length]
}

function stateColor(state) {
  const colors = {
    idle: '#64748b',
    writing: '#3b82f6',
    researching: '#8b5cf6',
    executing: '#f59e0b',
    syncing: '#06b6d4',
    reviewing: '#10b981',
    error: '#ef4444',
  }
  return colors[state] || '#64748b'
}

function truncate(str, max) {
  if (!str) return ''
  return str.length > max ? str.slice(0, max) + '...' : str
}
</script>

<style scoped>
.office-scene {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  position: relative;
}

.scene-svg {
  width: 100%;
  height: 100%;
  max-width: 1280px;
  max-height: 720px;
}

.agent-tooltip {
  position: absolute;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  font-size: 12px;
  pointer-events: none;
  z-index: 100;
  box-shadow: var(--shadow);
  min-width: 180px;
}

.tooltip-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.tooltip-name {
  font-weight: 600;
  color: var(--text-primary);
}

.tooltip-role {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: var(--accent);
  color: white;
}
.tooltip-role.manager {
  background: #f59e0b;
}

.tooltip-body > div {
  margin: 2px 0;
  color: var(--text-secondary);
}
</style>
