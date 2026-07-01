<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useInspection } from '../composables/useInspection.js'
import { useI18n } from '../composables/useI18n.js'
import { useAuditLog } from '../composables/useAuditLog.js'
import QcRunDialog from './QcRunDialog.vue'

const { batch, images, selectedId, loading, error, reviewedCount, currentBatchId, progress,
  needsRun, prepareBatch, runAndLoad, removeImage, resetAndReload, selectImage, toggleReviewed, isReviewed } = useInspection()
const { t } = useI18n()
const { log } = useAuditLog()

const route = useRoute()

const search = ref('')
const filterMode = ref('all')
const sortBy = ref('name')
const showRunDialog = ref(false)

async function loadFor(batchId) {
  if (!batchId) return
  try {
    await prepareBatch(batchId)
    if (batch.value) log('BATCH_LOADED', `Loaded batch ${batch.value.batch_name}`)
  } catch (e) {
    console.error(e)
  }
}

function onLoad() {
  if (needsRun.value) {
    showRunDialog.value = true
    return
  }
  loadFor(route.query.batch)
}

async function onRunConfirm({ confidenceThreshold }) {
  showRunDialog.value = false
  await runAndLoad(route.query.batch, confidenceThreshold)
  if (batch.value) log('BATCH_SENT', `Started QC segmentation: ${batch.value.batch_name}`)
}

async function onDeleteImage(img) {
  if (!confirm(t('qc.confirmDeleteImage'))) return
  await removeImage(img.id)
  log('IMAGE_DELETED', `Deleted image: ${img.filename}`)
}

function onRerun() {
  showRunDialog.value = true
}

async function onReset() {
  if (!confirm(t('qc.confirmReset'))) return
  await resetAndReload(route.query.batch)
  log('BATCH_RESET', `Reset batch ${currentBatchId.value}`)
}

onMounted(() => loadFor(route.query.batch))
watch(() => route.query.batch, (id) => loadFor(id))

const filteredImages = computed(() => {
  let result = images.value
  if (search.value) {
    const q = search.value.toLowerCase()
    result = result.filter((img) => img.filename.toLowerCase().includes(q))
  }
  if (filterMode.value === 'defect') result = result.filter((i) => i.status === 'defect')
  if (filterMode.value === 'clean') result = result.filter((i) => i.status === 'clean')
  if (filterMode.value === 'reviewed') result = result.filter((i) => isReviewed(i.id))
  if (filterMode.value === 'unreviewed') result = result.filter((i) => !isReviewed(i.id))

  const sorted = [...result]
  if (sortBy.value === 'name') {
    sorted.sort((a, b) => a.filename.localeCompare(b.filename))
  } else if (sortBy.value === 'defects') {
    sorted.sort((a, b) => b.defects.length - a.defects.length)
  }
  return sorted
})

function handleToggleReviewed(img) {
  const wasComplete = images.value.length > 0 && reviewedCount.value === images.value.length
  toggleReviewed(img.id)
  const action = isReviewed(img.id) ? 'IMAGE_REVIEWED' : 'IMAGE_UNREVIEWED'
  log(action, `${isReviewed(img.id) ? 'Marked' : 'Unmarked'} ${img.filename}`)
  const isComplete = images.value.length > 0 && reviewedCount.value === images.value.length
  if (isComplete && !wasComplete) {
    log('BATCH_REVIEWED', `Completed review: ${batch.value?.batch_name ?? ''}`)
  }
}
</script>

<template>
  <aside class="batch-sidebar">
    <div class="batch-head">
      <button class="btn-load" :disabled="loading" @click="onLoad">
        {{ loading ? t('qc.loadingBatch') : t('qc.loadBatch') }}
      </button>

      <div v-if="loading" class="skeleton-meta">
        <p class="progress-text mono">{{ progress.done }}/{{ progress.total }}</p>
        <div class="skeleton-line"></div>
        <div class="skeleton-line short"></div>
      </div>

      <div v-else-if="batch" class="batch-info">
        <p class="batch-name mono">{{ batch.batch_name }}</p>
        <p class="batch-path mono">{{ batch.source_path }}</p>
        <div class="progress-bar-wrap">
          <div class="progress-bar" :style="{ width: `${images.length ? (reviewedCount / images.length) * 100 : 0}%` }"></div>
        </div>
        <p class="progress-text">{{ t('qc.reviewProgress') }}: {{ reviewedCount }}/{{ images.length }}</p>
      </div>

      <div v-if="batch && !loading && !needsRun" class="batch-rerun-row">
        <button class="btn-secondary" @click="onRerun">{{ t('qc.rerun') }}</button>
        <button class="btn-secondary" @click="onReset">{{ t('qc.reset') }}</button>
      </div>

      <p v-else-if="needsRun" class="pending-hint">{{ t('qc.pendingHint') }}</p>

      <p v-if="error" class="error-msg">{{ t('common.error') }}: {{ error }}</p>
    </div>

    <QcRunDialog :show="showRunDialog" @cancel="showRunDialog = false" @confirm="onRunConfirm" />

    <div v-if="images.length" class="filter-section">
      <input v-model="search" class="search-input" :placeholder="t('qc.searchPlaceholder')" />
      <div class="filter-chips">
        <button :class="{ active: filterMode === 'all' }" @click="filterMode = 'all'">{{ t('qc.filterAll') }}</button>
        <button :class="{ active: filterMode === 'defect' }" @click="filterMode = 'defect'">{{ t('qc.filterDefect') }}</button>
        <button :class="{ active: filterMode === 'clean' }" @click="filterMode = 'clean'">{{ t('qc.filterClean') }}</button>
        <button :class="{ active: filterMode === 'unreviewed' }" @click="filterMode = 'unreviewed'">{{ t('qc.filterUnreviewed') }}</button>
      </div>
      <select v-model="sortBy" class="sort-select">
        <option value="name">{{ t('qc.sortName') }}</option>
        <option value="defects">{{ t('qc.sortDefects') }}</option>
      </select>
    </div>

    <ul class="batch-list">
      <li
        v-for="img in filteredImages"
        :key="img.id"
        class="batch-item"
        :class="{ active: img.id === selectedId, reviewed: isReviewed(img.id) }"
        @click="selectImage(img.id)"
      >
        <span class="dot" :class="img.status === 'defect' ? 'bad' : 'ok'"></span>
        <span class="fname mono">{{ img.filename }}</span>
        <span v-if="img.defects.length" class="count mono">{{ img.defects.length }}</span>
        <span v-if="isReviewed(img.id)" class="check-mark" title="Reviewed">&#10003;</span>
        <button
          class="img-del"
          :title="t('common.delete')"
          @click.stop="onDeleteImage(img)"
        >&times;</button>
      </li>
    </ul>

    <p v-if="!images.length && !loading" class="empty">{{ t('qc.batchEmpty') }}</p>
    <p v-if="images.length && !filteredImages.length" class="empty">{{ t('common.noResults') }}</p>
  </aside>
</template>

<style scoped>
.batch-sidebar {
  width: var(--sidebar-left);
  flex-shrink: 0;
  background: var(--color-canvas);
  border-right: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.batch-head {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-hairline);
}
.btn-load {
  width: 100%;
  padding: 9px 16px;
  cursor: pointer;
  background: var(--color-primary);
  color: var(--color-on-primary);
  border: none;
  font-family: var(--font-sans);
  font-size: 14px;
  letter-spacing: 0.16px;
}
.btn-load:hover {
  background: var(--color-primary-hover);
}
.btn-load:disabled {
  opacity: 0.5;
  cursor: default;
}
.batch-rerun-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.batch-rerun-row .btn-secondary {
  flex: 1;
  padding: 7px 12px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  cursor: pointer;
  font-family: var(--font-sans);
  font-size: 12px;
  letter-spacing: 0.16px;
}
.batch-rerun-row .btn-secondary:hover {
  background: var(--color-surface-1);
}
.skeleton-meta {
  margin-top: 12px;
}
.skeleton-line {
  height: 12px;
  background: var(--color-surface-2);
  margin-bottom: 6px;
  animation: pulse 1.2s ease-in-out infinite;
}
.skeleton-line.short {
  width: 60%;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}
.batch-info {
  margin-top: 12px;
}
.batch-name {
  font-size: 12px;
  color: var(--color-ink);
  margin: 0 0 4px;
  font-weight: 600;
  letter-spacing: 0.16px;
}
.batch-path {
  font-size: 11px;
  color: var(--color-ink-subtle);
  margin: 0 0 8px;
  word-break: break-all;
  letter-spacing: 0.16px;
}
.progress-bar-wrap {
  height: 4px;
  background: var(--color-surface-2);
}
.progress-bar {
  height: 100%;
  background: var(--color-success);
  transition: width 0.2s ease;
}
.progress-text {
  font-size: 11px;
  color: var(--color-ink-muted);
  margin: 4px 0 0;
  letter-spacing: 0.16px;
}
.error-msg {
  font-size: 12px;
  color: var(--color-error);
  margin: 8px 0 0;
  letter-spacing: 0.16px;
}
.pending-hint {
  font-size: 12px;
  color: var(--color-ink-muted);
  margin: 12px 0 0;
  letter-spacing: 0.16px;
}
.filter-section {
  padding: 8px 16px;
  border-bottom: 1px solid var(--color-hairline);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.search-input {
  padding: 6px 10px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  border-bottom: 2px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 13px;
  outline: none;
  letter-spacing: 0.16px;
}
.search-input:focus {
  border-bottom-color: var(--color-primary);
}
.filter-chips {
  display: flex;
  gap: 2px;
}
.filter-chips button {
  flex: 1;
  padding: 4px 6px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  font-family: var(--font-sans);
  font-size: 11px;
  cursor: pointer;
  letter-spacing: 0.16px;
}
.filter-chips button.active {
  background: var(--color-primary);
  color: var(--color-on-primary);
  border-color: var(--color-primary);
  font-weight: 600;
}
.sort-select {
  padding: 4px 8px;
  background: var(--color-surface-1);
  border: 1px solid var(--color-hairline);
  color: var(--color-ink);
  font-family: var(--font-sans);
  font-size: 12px;
  outline: none;
}
.batch-list {
  list-style: none;
  margin: 0;
  padding: 4px;
  overflow-y: auto;
  flex: 1;
}
.batch-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  cursor: pointer;
  border-left: 3px solid transparent;
  color: var(--color-ink-muted);
}
.batch-item:hover {
  background: var(--color-surface-1);
}
.batch-item.active {
  background: var(--color-surface-1);
  border-left-color: var(--color-primary);
  color: var(--color-ink);
}
.batch-item.reviewed {
  opacity: 0.6;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot.bad {
  background: var(--color-error);
}
.dot.ok {
  background: var(--color-success);
}
.fname {
  font-size: 13px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  letter-spacing: 0.16px;
}
.count {
  font-size: 11px;
  background: var(--color-error);
  color: var(--color-on-primary);
  padding: 0 5px;
  letter-spacing: 0.32px;
}
.check-mark {
  color: var(--color-success);
  font-size: 12px;
  font-weight: 600;
}
.img-del {
  width: 22px;
  height: 22px;
  background: transparent;
  border: 1px solid var(--color-hairline);
  color: var(--color-ink-muted);
  cursor: pointer;
  font-family: var(--font-sans);
  font-size: 16px;
  line-height: 18px;
  padding: 0;
}
.img-del:hover {
  border-color: var(--color-error);
  color: var(--color-error);
  background: var(--color-surface-1);
}
.empty {
  color: var(--color-ink-subtle);
  font-size: 14px;
  padding: 16px;
  letter-spacing: 0.16px;
}
.mono {
  font-family: var(--font-mono);
}
</style>
