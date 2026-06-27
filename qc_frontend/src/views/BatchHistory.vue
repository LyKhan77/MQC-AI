<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../composables/useI18n.js'
import { useBatchHistory } from '../composables/useBatchHistory.js'

const { t } = useI18n()
const router = useRouter()
const { batches, refresh } = useBatchHistory()

onMounted(refresh)

const search = ref('')
const statusFilter = ref('')

const filtered = computed(() => {
  let result = batches.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter((b) => b.name.toLowerCase().includes(q))
  }
  if (statusFilter.value) {
    result = result.filter((b) => b.status === statusFilter.value)
  }
  return result
})

function openBatch(batch) {
  router.push({ name: 'qc', query: { batch: batch.id } })
}

function formatDate(iso) {
  return new Date(iso).toLocaleString('id-ID', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const statusClass = (s) => `status-${s}`
</script>

<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t('batches.title') }}</h2>
      <p class="page-subtitle">{{ t('batches.subtitle') }}</p>
    </div>

    <div class="filter-bar">
      <input v-model="search" class="text-input" :placeholder="t('batches.searchPlaceholder')" />
      <select v-model="statusFilter" class="text-input">
        <option value="">{{ t('batches.filterAll') }}</option>
        <option value="reviewed">{{ t('batches.filterReviewed') }}</option>
        <option value="done">{{ t('batches.filterDone') }}</option>
        <option value="processing">{{ t('batches.filterProcessing') }}</option>
        <option value="failed">{{ t('batches.filterFailed') }}</option>
      </select>
    </div>

    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>{{ t('batches.columnName') }}</th>
            <th>{{ t('batches.columnCamera') }}</th>
            <th>{{ t('batches.columnDate') }}</th>
            <th>{{ t('batches.columnImages') }}</th>
            <th>{{ t('batches.columnDefects') }}</th>
            <th>{{ t('batches.columnReviewed') }}</th>
            <th>{{ t('batches.columnStatus') }}</th>
            <th>{{ t('batches.columnActions') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="batch in filtered" :key="batch.id">
            <td class="mono">{{ batch.name }}</td>
            <td>{{ batch.cameraName }}</td>
            <td class="mono">{{ formatDate(batch.createdAt) }}</td>
            <td>{{ batch.imageCount }}</td>
            <td>
              <span v-if="batch.defectCount" class="defect-num">{{ batch.defectCount }}</span>
              <span v-else class="clean-num">0</span>
            </td>
            <td class="mono">{{ batch.reviewedCount }}/{{ batch.imageCount }}</td>
            <td><span class="status-pill" :class="statusClass(batch.status)">{{ t(`batches.filter${batch.status.charAt(0).toUpperCase() + batch.status.slice(1)}`) }}</span></td>
            <td>
              <button class="btn-sm" @click="openBatch(batch)">{{ t('batches.open') }}</button>
              <button class="btn-sm" @click="router.push({ name: 'reports' })">{{ t('batches.generateReport') }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!filtered.length" class="empty-state">{{ t('batches.noBatches') }}</p>
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
.table-wrap {
  background: var(--color-canvas);
  border: 1px solid var(--color-hairline);
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}
.data-table th {
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
.data-table td {
  padding: 10px 16px;
  border-bottom: 1px solid var(--color-hairline);
  color: var(--color-ink);
}
.data-table tbody tr:hover {
  background: var(--color-surface-1);
}
.data-table tbody tr:last-child td {
  border-bottom: none;
}
.mono {
  font-family: var(--font-mono);
  font-size: 13px;
}
.defect-num {
  color: var(--color-error);
  font-weight: 600;
}
.clean-num {
  color: var(--color-success);
  font-weight: 600;
}
.status-pill {
  display: inline-block;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.32px;
}
.status-pill.status-reviewed {
  background: var(--color-success);
  color: var(--color-on-primary);
}
.status-pill.status-pending {
  background: var(--color-warning);
  color: var(--color-ink);
}
.status-pill.status-processing {
  background: var(--color-info);
  color: var(--color-on-primary);
}
.status-pill.status-done {
  background: var(--color-surface-1);
  color: var(--color-ink);
  border: 1px solid var(--color-hairline);
}
.status-pill.status-failed {
  background: var(--color-error);
  color: var(--color-on-primary);
}
.btn-sm {
  padding: 4px 12px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-primary);
  font-family: var(--font-sans);
  font-size: 12px;
  cursor: pointer;
  margin-right: 4px;
  letter-spacing: 0.16px;
}
.btn-sm:hover {
  background: var(--color-surface-1);
}
.empty-state {
  padding: 32px 16px;
  text-align: center;
  color: var(--color-ink-subtle);
  font-size: 14px;
}
</style>
