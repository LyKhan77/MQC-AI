<script setup>
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()

defineProps({
  collapsed: Boolean,
})

const emit = defineEmits(['toggle'])

const navItems = [
  { name: 'live', icon: 'M8 5v14l11-7z', labelKey: 'nav.liveMonitor' },
  { name: 'qc', icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5', labelKey: 'nav.qcStudio' },
  { name: 'batches', icon: 'M3 5h18M3 12h18M3 19h18', labelKey: 'nav.batchHistory' },
  { name: 'media', icon: 'M4 4h16v12H4z M8 20h8 M10 16v4 M8 8h8 M8 12h4', labelKey: 'nav.mediaDetection' },
  { name: 'reports', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M8 13h8M8 17h5', labelKey: 'nav.reports' },
  { name: 'audit', icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11', labelKey: 'nav.auditLog' },
  { name: 'settings', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6z M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z', labelKey: 'nav.settings' },
]
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <span class="brand-mark">GSPE</span>
      <span v-if="!collapsed" class="brand-divider" aria-hidden="true"></span>
      <span v-if="!collapsed" class="brand-text">MQC-AI</span>
    </div>

    <nav class="sidebar-nav">
      <router-link
        v-for="item in navItems"
        :key="item.name"
        :to="{ name: item.name }"
        class="nav-item"
        :title="t(item.labelKey)"
      >
        <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path :d="item.icon" />
        </svg>
        <span v-if="!collapsed" class="nav-label">{{ t(item.labelKey) }}</span>
      </router-link>
    </nav>

    <button class="collapse-btn" @click="emit('toggle')" :title="collapsed ? t('topbar.expand') : t('topbar.collapse')">
      <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <path v-if="collapsed" d="M9 18l6-6-6-6" />
        <path v-else d="M15 18l-6-6 6-6" />
      </svg>
    </button>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: 220px;
  flex-shrink: 0;
  background: var(--color-canvas);
  border-right: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  transition: width 0.15s ease;
  overflow: hidden;
}

.app-sidebar.collapsed {
  width: 56px;
}

.sidebar-header {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  border-bottom: 1px solid var(--color-hairline);
  flex-shrink: 0;
}

.app-sidebar.collapsed .sidebar-header {
  justify-content: center;
  padding: 0 4px;
}

.brand-mark {
  font-weight: 600;
  font-size: 16px;
  color: var(--color-primary);
  letter-spacing: 0;
  white-space: nowrap;
}

.brand-divider {
  width: 1px;
  height: 16px;
  background: var(--color-ink-subtle);
  flex-shrink: 0;
}

.brand-text {
  font-weight: 400;
  font-size: 14px;
  color: var(--color-ink-muted);
  letter-spacing: 0.16px;
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 8px 0;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: var(--color-ink-muted);
  text-decoration: none;
  font-size: 14px;
  letter-spacing: 0.16px;
  border-left: 3px solid transparent;
  transition: none;
}

.nav-item:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}

.nav-item.router-link-active {
  background: var(--color-surface-1);
  border-left-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
}

.collapse-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  border: none;
  border-top: 1px solid var(--color-hairline);
  background: transparent;
  color: var(--color-ink-muted);
  cursor: pointer;
  flex-shrink: 0;
}

.collapse-btn:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}
</style>
