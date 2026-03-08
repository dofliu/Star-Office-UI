<template>
  <div class="app" :class="[`theme-${currentTheme}`]">
    <!-- Top Navigation Bar -->
    <header class="top-bar">
      <div class="top-bar-left">
        <h1 class="app-title">{{ t('appTitle') }}</h1>
        <span class="app-subtitle">{{ t('subtitle') }}</span>
        <span class="connection-indicator" :class="{ connected: wsConnected }">
          {{ wsConnected ? '●' : '○' }}
        </span>
      </div>
      <div class="top-bar-center">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ t(tab.label) }}</span>
        </button>
      </div>
      <div class="top-bar-right">
        <div class="lang-switcher">
          <button
            v-for="lang in availableLocales"
            :key="lang"
            class="lang-btn"
            :class="{ active: locale === lang }"
            @click="setLocale(lang)"
          >{{ langLabels[lang] }}</button>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="main-content">
      <!-- Office Scene View -->
      <div class="scene-area" v-show="activeTab === 'office'">
        <OfficeScene
          :agents="agents"
          :theme="currentTheme"
          :themes="themes"
          @switch-theme="switchTheme"
        />
      </div>

      <!-- Agents + Tasks Split View -->
      <div class="dashboard-area" v-show="activeTab === 'dashboard'">
        <div class="dashboard-grid">
          <AgentPanel :agents="agents" :t="t" />
          <TaskBoard :tasks="allTasks" :agents="agents" :t="t" @refresh="refreshTasks" />
        </div>
      </div>

      <!-- History View -->
      <div class="history-area" v-show="activeTab === 'history'">
        <HistoryPanel :agents="agents" :t="t" />
      </div>

      <!-- Scenes View -->
      <div class="scenes-area" v-show="activeTab === 'scenes'">
        <ScenePicker :themes="themes" :currentTheme="currentTheme" :t="t" @select="switchTheme" />
      </div>
    </main>

    <!-- Status Bar -->
    <footer class="status-bar">
      <div class="status-left">
        <span class="agent-count">{{ onlineAgents.length }} {{ t('agents') }} {{ t('online') }}</span>
        <span class="separator">|</span>
        <span class="working-count">{{ workingAgents.length }} {{ t('in_progress') }}</span>
      </div>
      <div class="status-right">
        <span class="active-tasks">{{ activeTasks.length }} {{ t('tasks') }}</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from './i18n/index.js'
import { useAgents } from './composables/useAgents.js'
import { useTasks } from './composables/useTasks.js'
import { useWebSocket } from './composables/useWebSocket.js'
import OfficeScene from './components/OfficeScene.vue'
import AgentPanel from './components/AgentPanel.vue'
import TaskBoard from './components/TaskBoard.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import ScenePicker from './components/ScenePicker.vue'

const { t, locale, setLocale, availableLocales } = useI18n()
const { agents, onlineAgents, workingAgents, startPolling, stopPolling, setupWebSocket } = useAgents()
const { tasks: allTasks, activeTasks, fetchTasks } = useTasks()
const { connected: wsConnected } = useWebSocket()

const langLabels = { zh: '中', en: 'En', ja: '日' }
const activeTab = ref('office')
const currentTheme = ref(localStorage.getItem('claw-office-theme') || 'modern-office')

const themes = ref([])

const tabs = [
  { id: 'office', icon: '🏢', label: 'scenes' },
  { id: 'dashboard', icon: '📊', label: 'agents' },
  { id: 'history', icon: '📋', label: 'history' },
  { id: 'scenes', icon: '🎨', label: 'switchTheme' },
]

function switchTheme(themeId) {
  currentTheme.value = themeId
  localStorage.setItem('claw-office-theme', themeId)
}

async function fetchThemes() {
  try {
    const res = await fetch('/api/scenes')
    const data = await res.json()
    themes.value = data.themes || []
  } catch (e) {
    console.error('Failed to fetch themes:', e)
  }
}

function refreshTasks() {
  fetchTasks()
}

onMounted(() => {
  startPolling(3000)
  setupWebSocket()
  fetchTasks()
  fetchThemes()
})

onUnmounted(() => {
  stopPolling()
})
</script>

<style>
/* === Global Reset & Variables === */
:root {
  --bg-primary: #0f172a;
  --bg-secondary: #1e293b;
  --bg-card: #1e293b;
  --bg-card-hover: #334155;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #3b82f6;
  --accent-hover: #2563eb;
  --success: #22c55e;
  --warning: #f59e0b;
  --error: #ef4444;
  --border: #334155;
  --radius: 8px;
  --radius-lg: 12px;
  --shadow: 0 4px 6px -1px rgba(0,0,0,0.3);
  --font-mono: 'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
  height: 100vh;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* === Layout === */
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
}

.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 52px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--accent);
  font-family: var(--font-mono);
}

.app-subtitle {
  font-size: 12px;
  color: var(--text-muted);
}

.connection-indicator {
  font-size: 10px;
  color: var(--error);
  transition: color 0.3s;
}
.connection-indicator.connected {
  color: var(--success);
}

.top-bar-center {
  display: flex;
  gap: 4px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}
.tab-btn:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
.tab-btn.active {
  background: var(--accent);
  color: white;
}
.tab-icon { font-size: 14px; }

.lang-switcher {
  display: flex;
  gap: 4px;
}
.lang-btn {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}
.lang-btn:hover { border-color: var(--accent); color: var(--text-primary); }
.lang-btn.active { background: var(--accent); border-color: var(--accent); color: white; }

.main-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}

.scene-area,
.dashboard-area,
.history-area,
.scenes-area {
  position: absolute;
  inset: 0;
  overflow: auto;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  padding: 16px;
  height: 100%;
}

.status-bar {
  display: flex;
  justify-content: space-between;
  padding: 0 20px;
  height: 28px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-muted);
  align-items: center;
  flex-shrink: 0;
}
.separator { margin: 0 8px; }

/* === Scrollbar === */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }
</style>
