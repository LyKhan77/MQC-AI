<script setup>
import { ref, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import InferenceIcon from './icons/InferenceIcon.vue'
import LiveMonitorIcon from './icons/LiveMonitorIcon.vue'
import MediaDetectionIcon from './icons/MediaDetectionIcon.vue'
import QuantityIcon from './icons/QuantityIcon.vue'
import QuantityDetectionIcon from './icons/QuantityDetectionIcon.vue'
import QuantityHistoryIcon from './icons/QuantityHistoryIcon.vue'
import QualityControlIcon from './icons/QualityControlIcon.vue'
import DirectInspectionIcon from './icons/DirectInspectionIcon.vue'
import QcStudioIcon from './icons/QcStudioIcon.vue'
import BatchHistoryIcon from './icons/BatchHistoryIcon.vue'
import ReportsIcon from './icons/ReportsIcon.vue'
import AuditLogIcon from './icons/AuditLogIcon.vue'
import SettingsIcon from './icons/SettingsIcon.vue'
import ChevronRightIcon from './icons/ChevronRightIcon.vue'
import PanelCollapseIcon from './icons/PanelCollapseIcon.vue'
import PanelExpandIcon from './icons/PanelExpandIcon.vue'

const { t } = useI18n()
const route = useRoute()

const props = defineProps({
  collapsed: Boolean,
})

const emit = defineEmits(['toggle'])

const nav = [
  {
    key: 'inference',
    labelKey: 'nav.inference',
    icon: InferenceIcon,
    children: [
      { name: 'live', icon: LiveMonitorIcon, labelKey: 'nav.liveMonitor' },
      { name: 'media', icon: MediaDetectionIcon, labelKey: 'nav.mediaDetection' },
    ],
  },
  {
    key: 'quantity',
    labelKey: 'nav.quantity',
    icon: QuantityIcon,
    children: [
      { name: 'quantity', icon: QuantityDetectionIcon, labelKey: 'nav.quantityDetection' },
      { name: 'quantity-history', icon: QuantityHistoryIcon, labelKey: 'nav.quantityHistory' },
    ],
  },
  {
    key: 'quality',
    labelKey: 'nav.qualityControl',
    icon: QualityControlIcon,
    children: [
      { name: 'direct-inspection', icon: DirectInspectionIcon, labelKey: 'nav.directInspection' },
      { name: 'measurement', icon: DirectInspectionIcon, labelKey: 'nav.inspectMeasurement' },
      { name: 'qc', icon: QcStudioIcon, labelKey: 'nav.qcStudio' },
      { name: 'batches', icon: BatchHistoryIcon, labelKey: 'nav.batchHistory' },
    ],
  },
  {
    key: 'records',
    labelKey: 'nav.records',
    icon: AuditLogIcon,
    children: [
      { name: 'reports', icon: ReportsIcon, labelKey: 'nav.reports' },
      { name: 'audit', icon: AuditLogIcon, labelKey: 'nav.auditLog' },
    ],
  },
  { name: 'settings', icon: SettingsIcon, labelKey: 'nav.settings' },
]

const groups = nav.filter((n) => n.children)
const sidebarNav = ref(null)
const focusedIndex = ref(-1)

function groupActive(group) {
  return group.children.some((c) => c.name === route.name)
}

const expanded = ref(Object.fromEntries(groups.map((g) => [g.key, groupActive(g)])))

function toggleGroup(key) {
  expanded.value = { ...expanded.value, [key]: !expanded.value[key] }
}

function focusableElements() {
  const items = sidebarNav.value?.querySelectorAll('.nav-item, .nav-group-header')
  return Array.from(items ?? []).filter((item) => {
    const parent = item.closest('.nav-children')
    return !parent || parent.style.display !== 'none'
  })
}

function focusItem(index) {
  const items = focusableElements()
  if (index < 0 || index >= items.length) return
  focusedIndex.value = index
  items[index].focus()
}

function syncFocusedIndex(event) {
  const items = focusableElements()
  focusedIndex.value = items.indexOf(event.target)
}

function onKeydown(event) {
  const items = focusableElements()
  if (!items.length) return

  const targetIndex = items.indexOf(event.target)
  if (targetIndex >= 0) focusedIndex.value = targetIndex
  if (focusedIndex.value < 0) focusedIndex.value = 0

  if (event.key === 'ArrowDown') {
    event.preventDefault()
    focusItem(Math.min(focusedIndex.value + 1, items.length - 1))
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    focusItem(Math.max(focusedIndex.value - 1, 0))
  } else if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    items[focusedIndex.value]?.click()
  }
}

watch(
  () => route.name,
  () => {
    for (const g of groups) {
      if (groupActive(g) && !expanded.value[g.key]) {
        expanded.value = { ...expanded.value, [g.key]: true }
      }
    }

    nextTick(() => {
      if (focusedIndex.value >= 0) return
      const items = focusableElements()
      const activeIndex = items.findIndex((el) => el.classList.contains('router-link-active'))
      if (activeIndex >= 0) focusedIndex.value = activeIndex
    })
  },
  { immediate: true },
)
</script>

<template>
  <aside class="app-sidebar" :class="{ collapsed: props.collapsed }">
    <div class="sidebar-header">
      <span class="brand-mark">GSPE</span>
      <span v-if="!props.collapsed" class="brand-divider" aria-hidden="true"></span>
      <span v-if="!props.collapsed" class="brand-text">MQC-AI</span>
    </div>

    <nav
      ref="sidebarNav"
      class="sidebar-nav"
      @focus.capture="syncFocusedIndex"
      @focusin="syncFocusedIndex"
      @keydown="onKeydown"
    >
      <template v-if="props.collapsed">
        <template v-for="entry in nav" :key="entry.key || entry.name">
          <div v-if="entry.children" class="collapsed-group" :class="{ active: groupActive(entry) }">
            <router-link
              v-for="item in entry.children"
              :key="item.name"
              :to="{ name: item.name }"
              class="nav-item"
              :title="t(item.labelKey)"
              :aria-label="t(item.labelKey)"
              @focus="syncFocusedIndex"
            >
              <component :is="item.icon" class="nav-icon" />
            </router-link>
          </div>

          <div v-else class="collapsed-single">
            <router-link
              :to="{ name: entry.name }"
              class="nav-item"
              :title="t(entry.labelKey)"
              :aria-label="t(entry.labelKey)"
              @focus="syncFocusedIndex"
            >
              <component :is="entry.icon" class="nav-icon" />
            </router-link>
          </div>
        </template>
      </template>

      <template v-else>
        <template v-for="entry in nav" :key="entry.key || entry.name">
          <div
            v-if="entry.children"
            class="nav-group"
            :class="{ active: groupActive(entry), open: expanded[entry.key] }"
          >
            <button
              type="button"
              class="nav-item nav-group-header"
              tabindex="0"
              :aria-expanded="!!expanded[entry.key]"
              @focus="syncFocusedIndex"
              @click="toggleGroup(entry.key)"
            >
              <component :is="entry.icon" class="nav-icon" />
              <span class="nav-label">{{ t(entry.labelKey) }}</span>
              <ChevronRightIcon class="nav-chevron" :class="{ rot: expanded[entry.key] }" />
            </button>

            <div v-show="expanded[entry.key]" class="nav-children">
              <router-link
                v-for="child in entry.children"
                :key="child.name"
                :to="{ name: child.name }"
                class="nav-item nav-child"
                :title="t(child.labelKey)"
                @focus="syncFocusedIndex"
              >
                <component :is="child.icon" class="nav-icon" />
                <span class="nav-label">{{ t(child.labelKey) }}</span>
              </router-link>
            </div>
          </div>

          <router-link
            v-else
            :to="{ name: entry.name }"
            class="nav-item"
            :title="t(entry.labelKey)"
            @focus="syncFocusedIndex"
          >
            <component :is="entry.icon" class="nav-icon" />
            <span class="nav-label">{{ t(entry.labelKey) }}</span>
          </router-link>
        </template>
      </template>
    </nav>

    <button
      class="collapse-btn"
      :title="props.collapsed ? t('topbar.expand') : t('topbar.collapse')"
      @click="emit('toggle')"
    >
      <PanelExpandIcon v-if="props.collapsed" class="nav-icon" />
      <PanelCollapseIcon v-else class="nav-icon" />
    </button>
  </aside>
</template>

<style scoped>
.app-sidebar {
  width: var(--sidebar-left);
  flex-shrink: 0;
  background: var(--color-canvas);
  border-right: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  transition: width 0.15s ease;
  overflow: hidden;
}

.app-sidebar.collapsed {
  width: 64px;
  overflow: visible;
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
  font-size: 15px;
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
  font-size: 15px;
  letter-spacing: 0.16px;
  border-left: 3px solid transparent;
  transition: none;
}

.nav-item:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}

.nav-item:focus-visible,
.nav-group-header:focus-visible,
.collapse-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
  position: relative;
  z-index: 1;
}

.nav-item.router-link-active {
  background: var(--color-surface-1);
  border-left-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-icon {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
}

.nav-label {
  white-space: nowrap;
  overflow: hidden;
  flex: 1;
}

.nav-group-header {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  color: var(--color-ink-muted);
  text-decoration: none;
  font-size: 15px;
  letter-spacing: 0.16px;
  border-left: 3px solid transparent;
  background: transparent;
  border: none;
  cursor: pointer;
  font-family: inherit;
}

.nav-group-header:hover {
  background: var(--color-surface-1);
  color: var(--color-ink);
}

.nav-group.active .nav-group-header {
  background: var(--color-surface-1);
  color: var(--color-primary);
  font-weight: 600;
}

.nav-chevron {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
  color: currentColor;
  transition: transform 0.15s ease;
}

.nav-chevron.rot {
  transform: rotate(90deg);
}

@media (prefers-reduced-motion: reduce) {
  .app-sidebar,
  .nav-chevron {
    transition: none;
  }
}

.nav-children {
  display: flex;
  flex-direction: column;
}

.nav-child {
  padding-left: 44px;
}

.nav-child .nav-icon {
  width: 20px;
  height: 20px;
}

.app-sidebar.collapsed .nav-item {
  justify-content: center;
  width: 100%;
  min-height: 48px;
  padding: 12px 0;
}

.app-sidebar.collapsed .nav-icon {
  width: 24px;
  height: 24px;
}

.app-sidebar.collapsed .sidebar-nav {
  overflow-x: hidden;
}

.app-sidebar.collapsed .collapsed-group,
.app-sidebar.collapsed .collapsed-single {
  width: 100%;
}

.app-sidebar.collapsed .collapsed-group + .collapsed-group,
.app-sidebar.collapsed .collapsed-group + .collapsed-single {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--color-hairline);
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
