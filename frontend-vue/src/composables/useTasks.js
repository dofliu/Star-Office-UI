import { ref, computed } from 'vue'

const tasks = ref([])
const loading = ref(false)

export function useTasks() {
  const activeTasks = computed(() =>
    tasks.value.filter(t => ['pending', 'assigned', 'in_progress'].includes(t.status))
  )
  const completedTasks = computed(() =>
    tasks.value.filter(t => t.status === 'completed')
  )

  async function fetchTasks(filters = {}) {
    loading.value = true
    try {
      const params = new URLSearchParams(filters)
      const res = await fetch(`/api/tasks?${params}`)
      const data = await res.json()
      tasks.value = data.tasks || []
    } catch (e) {
      console.error('Failed to fetch tasks:', e)
    } finally {
      loading.value = false
    }
  }

  async function createTask(taskData) {
    const res = await fetch('/api/tasks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskData),
    })
    const data = await res.json()
    if (data.task) {
      tasks.value.unshift(data.task)
    }
    return data
  }

  async function assignTask(taskId, agentId) {
    const res = await fetch(`/api/tasks/${taskId}/assign`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agentId }),
    })
    const data = await res.json()
    if (data.task) {
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx >= 0) tasks.value[idx] = data.task
    }
    return data
  }

  async function updateTaskStatus(taskId, status, progress, result) {
    const res = await fetch(`/api/tasks/${taskId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, progress, result }),
    })
    const data = await res.json()
    if (data.task) {
      const idx = tasks.value.findIndex(t => t.id === taskId)
      if (idx >= 0) tasks.value[idx] = data.task
    }
    return data
  }

  return {
    tasks,
    activeTasks,
    completedTasks,
    loading,
    fetchTasks,
    createTask,
    assignTask,
    updateTaskStatus,
  }
}
