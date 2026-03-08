import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useWebSocket } from './useWebSocket'

const agents = ref([])
const loading = ref(false)
let pollInterval = null

export function useAgents() {
  const ws = useWebSocket()

  const manager = computed(() => agents.value.find(a => a.role === 'manager'))
  const workers = computed(() => agents.value.filter(a => a.role === 'worker'))
  const onlineAgents = computed(() => agents.value.filter(a => a.auth_status !== 'offline'))
  const workingAgents = computed(() =>
    agents.value.filter(a => !['idle', 'error'].includes(a.state) && a.auth_status !== 'offline')
  )

  async function fetchAgents() {
    try {
      const res = await fetch('/api/agents')
      const data = await res.json()
      agents.value = data.agents || []
    } catch (e) {
      console.error('Failed to fetch agents:', e)
    }
  }

  function startPolling(intervalMs = 3000) {
    fetchAgents()
    pollInterval = setInterval(fetchAgents, intervalMs)
  }

  function stopPolling() {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }

  function setupWebSocket() {
    ws.connect()
    ws.on('agent.state_changed', (data) => {
      const idx = agents.value.findIndex(a => a.id === data.id)
      if (idx >= 0) {
        agents.value[idx] = { ...agents.value[idx], ...data }
      }
    })
    ws.on('agent.joined', (data) => {
      const idx = agents.value.findIndex(a => a.id === data.id)
      if (idx < 0) {
        agents.value.push(data)
      }
    })
    ws.on('agent.left', (data) => {
      const idx = agents.value.findIndex(a => a.id === data.agentId)
      if (idx >= 0) {
        agents.value[idx].auth_status = 'offline'
        agents.value[idx].state = 'idle'
      }
    })
  }

  return {
    agents,
    manager,
    workers,
    onlineAgents,
    workingAgents,
    loading,
    fetchAgents,
    startPolling,
    stopPolling,
    setupWebSocket,
  }
}
