<template>
  <div class="scene-picker">
    <div class="picker-header">
      <h2>{{ t('switchTheme') }}</h2>
    </div>
    <div class="themes-grid">
      <div v-for="theme in themes" :key="theme.id"
           class="theme-card" :class="{ active: theme.id === currentTheme }"
           @click="$emit('select', theme.id)">
        <div class="theme-preview" :style="{ background: previewBg(theme.id) }">
          <div class="theme-overlay">
            <span class="theme-icon">{{ themeIcon(theme.id) }}</span>
          </div>
        </div>
        <div class="theme-info">
          <div class="theme-name">{{ theme.name?.[locale] || theme.name?.en || theme.id }}</div>
          <div class="theme-desc">{{ theme.description?.[locale] || theme.description?.en || '' }}</div>
        </div>
        <div class="active-badge" v-if="theme.id === currentTheme">Active</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useI18n } from '../i18n/index.js'

const props = defineProps({
  themes: { type: Array, default: () => [] },
  currentTheme: { type: String, default: 'modern-office' },
  t: { type: Function, required: true },
})

defineEmits(['select'])
const { locale } = useI18n()

const previewColors = {
  'modern-office': 'linear-gradient(135deg, #1a2332, #2d3748)',
  'konoha-village': 'linear-gradient(135deg, #2d1f0e, #4a3520)',
  'pixel-classic': 'linear-gradient(135deg, #1e293b, #334155)',
  'classroom': 'linear-gradient(135deg, #f5f0e1, #d4c5a0)',
  'meeting-room': 'linear-gradient(135deg, #1c2433, #3a4555)',
  'resort': 'linear-gradient(135deg, #0e4a6e, #7dd3fc)',
}

const themeIcons = {
  'modern-office': '🏢',
  'konoha-village': '🍃',
  'pixel-classic': '👾',
  'classroom': '📚',
  'meeting-room': '💼',
  'resort': '🏖️',
}

function previewBg(id) {
  return previewColors[id] || 'linear-gradient(135deg, #1e293b, #334155)'
}

function themeIcon(id) {
  return themeIcons[id] || '🎨'
}
</script>

<style scoped>
.scene-picker {
  height: 100%;
  overflow-y: auto;
}

.picker-header {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-secondary);
}
.picker-header h2 { font-size: 14px; }

.themes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 20px;
}

.theme-card {
  background: var(--bg-secondary);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}
.theme-card:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}
.theme-card.active {
  border-color: var(--accent);
}

.theme-preview {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.theme-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.2);
}

.theme-icon {
  font-size: 48px;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3));
}

.theme-info {
  padding: 12px 14px;
}

.theme-name {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
}

.theme-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.active-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: var(--accent);
  color: white;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}
</style>
