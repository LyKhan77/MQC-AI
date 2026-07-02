<script setup>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from '../composables/useI18n.js'
import { useQuantityHistory } from '../composables/useQuantityHistory.js'
import { checksToCsv } from '../utils/quantity.js'
import { downloadBlob } from '../utils/export.js'

const { t } = useI18n()
const { checks, refresh } = useQuantityHistory()

onMounted(refresh)

const search = ref('')
const verdictFilter = ref('')

const filtered = computed(() => {
  let result = checks.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter((c) => (c.model_used || '').toLowerCase().includes(q) || (c.id || '').toLowerCase().includes(q))
  }
  if (verdictFilter.value) {
    result = result.filter((c) => c.verdict === verdictFilter.value)
  }
  return result
})

function exportCsv() {
  const csv = checksToCsv(filtered.value)
  downloadBlob(new Blob([csv], { type: 'text/csv' }), 'quantity_history.csv')
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('id-ID', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('quantity.historyTitle') }}</h2>
      <p class="page-subtitle">{{ t('quantity.historySubtitle') }}</p>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="text-input" :placeholder="t('quantity.searchPlaceholder')" />
      <select v-model="verdictFilter" class="text-input">
        <option value="">{{ t('quantity.filterAll') }}</option>
        <option value="pass">{{ t('quantity.pass') }}</option>
        <option value="fail">{{ t('quantity.fail') }}</option>
      </select>
      <button class="btn-sm" @click="exportCsv">{{ t('quantity.exportCsv') }}</button>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('quantity.colId') }}</th>
            <th>{{ t('quantity.colDate') }}</th>
            <th>{{ t('quantity.colModel') }}</th>
            <th>{{ t('quantity.total') }}</th>
            <th>{{ t('quantity.expectedTotal') }}</th>
            <th>{{ t('quantity.colVerdict') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in filtered" :key="c.id">
            <td class="mono">{{ c.id }}</td>
            <td class="mono">{{ formatDate(c.created_at) }}</td>
            <td>{{ c.model_used }}</td>
            <td class="mono">{{ c.total_count }}</td>
            <td class="mono">{{ c.expected_total ?? '-' }}</td>
            <td><span v-if="c.verdict !== 'none'" class="status-pill" :class="c.verdict === 'pass' ? 'verdict-pass' : 'verdict-fail'">{{ c.verdict === 'pass' ? t('quantity.pass') : t('quantity.fail') }}</span><span v-else>-</span></td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="empty-state">{{ t('quantity.noChecks') }}</p>
    </div>
  </div>
</template>

<style scoped>
.verdict-pass { background: var(--color-success); color: var(--color-on-primary); }
.verdict-fail { background: var(--color-error); color: var(--color-on-primary); }
.mono { font-family: var(--font-mono); }
</style>
