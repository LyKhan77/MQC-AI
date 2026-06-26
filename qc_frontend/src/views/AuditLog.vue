<script setup>
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import { ref, computed, onMounted } from 'vue'

const { t } = useI18n()
const { logs, refresh } = useAuditLog()
onMounted(refresh)

const search = ref('')
const filterAction = ref('')

const actionTypes = computed(() => {
  const set = new Set(logs.value.map((l) => l.action))
  return [...set].sort()
})

const filtered = computed(() => {
  let result = logs.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter(
      (l) => l.detail.toLowerCase().includes(q) || l.user.toLowerCase().includes(q),
    )
  }
  if (filterAction.value) {
    result = result.filter((l) => l.action === filterAction.value)
  }
  return result
})

function formatTime(iso) {
  const d = new Date(iso)
  return d.toLocaleString('id-ID', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('audit.title') }}</h2>
      <p class="page-subtitle">{{ t('audit.subtitle') }}</p>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="text-input" :placeholder="t('audit.searchPlaceholder')" />
      <select v-model="filterAction" class="text-input">
        <option value="">{{ t('audit.filterAll') }}</option>
        <option v-for="a in actionTypes" :key="a" :value="a">
          {{ t(`audit.actions.${a}`) }}
        </option>
      </select>
    </div>

    <div class="log-table-wrap">
      <table class="log-table">
        <thead>
          <tr>
            <th>{{ t('audit.columnTime') }}</th>
            <th>{{ t('audit.columnUser') }}</th>
            <th>{{ t('audit.columnAction') }}</th>
            <th>{{ t('audit.columnDetail') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="entry in filtered" :key="entry.id">
            <td class="mono">{{ formatTime(entry.timestamp) }}</td>
            <td>{{ entry.user }}</td>
            <td><span class="action-tag">{{ t(`audit.actions.${entry.action}`) }}</span></td>
            <td>{{ entry.detail }}</td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="empty-state">{{ t('audit.noEntries') }}</p>
    </div>
  </div>
</template>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.text-input {
  padding: 8px 12px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 14px;
  outline: none;
  letter-spacing: 0.16px;
}
.text-input:focus {
  border-bottom-color: var(--color-primary);
}
.text-input:first-child {
  flex: 1;
}
.log-table-wrap {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
}
.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.log-table th {
  text-align: left;
  padding: 12px 16px;
  font-weight: 600;
  font-size: 12px;
  color: var(--color-ink-muted);
  letter-spacing: 0.32px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--color-hairline);
  background: var(--color-surface-1);
}
.log-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}
.log-table tbody tr:hover {
  background: var(--color-surface-1);
}
.log-table tbody tr:last-child td {
  border-bottom: none;
}
.action-tag {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  background: var(--color-surface-2);
  color: var(--color-ink);
  letter-spacing: 0.16px;
}
.mono {
  font-family: var(--font-mono);
  font-size: 12px;
  white-space: nowrap;
}
.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-ink-subtle);
  font-size: 14px;
}
</style>
