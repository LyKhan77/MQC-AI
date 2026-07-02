<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'

const { t } = useI18n()
const route = useRoute()

defineProps({
  collapsed: Boolean,
})

const emit = defineEmits(['toggle'])

// Grouped navigation. A group entry has `children`; a leaf entry has `name`.
// When the sidebar is collapsed we flatten to leaf icons (see collapsedItems).
const nav = [
  {
    key: 'inference',
    labelKey: 'nav.inference',
    icon: 'M2 12h4l3 8 4-16 3 8h6',
    children: [
      { name: 'live', icon: 'M8 5v14l11-7z', labelKey: 'nav.liveMonitor' },
      { name: 'media', icon: 'M4 4h16v12H4z M8 20h8 M10 16v4 M8 8h8 M8 12h4', labelKey: 'nav.mediaDetection' },
    ],
  },
  {
    key: 'quantity',
    labelKey: 'nav.quantity',
    icon: 'M4 7h16M4 12h16M4 17h10 M7 4v3 M12 4v3 M17 4v3',
    children: [
      { name: 'quantity', icon: 'M4 7h16M4 12h16M4 17h10', labelKey: 'nav.quantityDetection' },
      { name: 'quantity-history', icon: 'M3 5h18M3 12h18M3 19h12', labelKey: 'nav.quantityHistory' },
    ],
  },
  {
    key: 'quality',
    labelKey: 'nav.qualityControl',
    icon: 'M12 3l8 4v5c0 5-3.4 8.5-8 10-4.6-1.5-8-5-8-10V7z M9 12l2 2 4-4',
    children: [
      { name: 'qc', icon: 'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5', labelKey: 'nav.qcStudio' },
      { name: 'batches', icon: 'M3 5h18M3 12h18M3 19h18', labelKey: 'nav.batchHistory' },
    ],
  },
  {
    key: 'records',
    labelKey: 'nav.records',
    icon: 'M3 7h18v4H3z M5 11h14v9H5z M9 15h6',
    children: [
      { name: 'reports', icon: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M8 13h8M8 17h5', labelKey: 'nav.reports' },
      { name: 'audit', icon: 'M9 11l3 3L22 4 M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11', labelKey: 'nav.auditLog' },
    ],
  },
  { name: 'settings', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6z M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 01-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z', labelKey: 'nav.settings' },
]

const groups = nav.filter((n) => n.children)

// Flattened leaves, in visual order, for the collapsed (icon-only) rail.
const collapsedItems = computed(() =>
  nav.flatMap((entry) => (entry.children ? entry.children : [entry])),
)

function groupActive(group) {
  return group.children.some((c) => c.name === route.name)
}

// Track which groups are open. Start with the group holding the active route open.
const expanded = ref(
  Object.fromEntries(groups.map((g) => [g.key, groupActive(g)])),
)

function toggleGroup(key) {
  expanded.value = { ...expanded.value, [key]: !expanded.value[key] }
}

// Navigating into a group's page always reveals that group.
watch(
  () => route.name,
  () => {
    for (const g of groups) {
      if (groupActive(g) && !expanded.value[g.key]) {
        expanded.value = { ...expanded.value, [g.key]: true }
      }
    }
  },
)
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed }">
    <div class="sidebar-header">
      <span class="brand-mark">GSPE</span>
      <span v-if="!collapsed" class="brand-divider" aria-hidden="true"></span>
      <span v-if="!collapsed" class="brand-text">MQC-AI</span>
    </div>

    <nav class="sidebar-nav">
      <!-- Collapsed: flat icon rail (quick access). -->
      <template v-if="collapsed">
        <router-link
          v-for="item in collapsedItems"
          :key="item.name"
          :to="{ name: item.name }"
          class="nav-item"
          :title="t(item.labelKey)"
        >
          <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
            <path :d="item.icon" />
          </svg>
        </router-link>
      </template>

      <!-- Expanded: grouped dropdowns + standalone leaves. -->
      <template v-else>
        <template v-for="entry in nav" :key="entry.key || entry.name">
          <div v-if="entry.children" class="nav-group" :class="{ active: groupActive(entry), open: expanded[entry.key] }">
            <button
              type="button"
              class="nav-item nav-group-header"
              :aria-expanded="!!expanded[entry.key]"
              @click="toggleGroup(entry.key)"
            >
              <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path :d="entry.icon" />
              </svg>
              <span class="nav-label">{{ t(entry.labelKey) }}</span>
              <svg class="nav-chevron" :class="{ rot: expanded[entry.key] }" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 6l6 6-6 6" />
              </svg>
            </button>

            <div v-show="expanded[entry.key]" class="nav-children">
              <router-link
                v-for="child in entry.children"
                :key="child.name"
                :to="{ name: child.name }"
                class="nav-item nav-child"
                :title="t(child.labelKey)"
              >
                <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path :d="child.icon" />
                </svg>
                <span class="nav-label">{{ t(child.labelKey) }}</span>
              </router-link>
            </div>
          </div>

          <router-link
            v-else
            :to="{ name: entry.name }"
            class="nav-item"
            :title="t(entry.labelKey)"
          >
            <svg class="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path :d="entry.icon" />
            </svg>
            <span class="nav-label">{{ t(entry.labelKey) }}</span>
          </router-link>
        </template>
      </template>
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
  flex: 1;
}

/* Group header (dropdown toggle) */
.nav-group-header {
  width: 100%;
  background: transparent;
  border: none;
  border-left: 3px solid transparent;
  cursor: pointer;
  font-family: inherit;
}

.nav-group.active .nav-group-header {
  color: var(--color-ink);
}

.nav-chevron {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: var(--color-ink-subtle);
  transition: transform 0.15s ease;
}

.nav-chevron.rot {
  transform: rotate(90deg);
}

@media (prefers-reduced-motion: reduce) {
  .nav-chevron {
    transition: none;
  }
}

/* Child links inside an open group */
.nav-children {
  display: flex;
  flex-direction: column;
}

.nav-child {
  padding-left: 32px;
}

.nav-child .nav-icon {
  width: 18px;
  height: 18px;
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
