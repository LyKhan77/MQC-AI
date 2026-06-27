import { ref, computed } from 'vue'
import { pollBatchUntilDone, getBatchResult, patchImageReviewed, patchBatch } from '../api/batches.js'

const STORAGE_KEY = 'mqc-reviewed'

const REVIEWER = 'inspector@gspemail.com'

const batch = ref(null)
const selectedId = ref(null)
const hoveredDefectId = ref(null)
const loading = ref(false)
const error = ref(null)
const reviewed = ref(new Set())
const currentBatchId = ref(null)
const progress = ref({ done: 0, total: 0 })
const lastAllReviewed = ref(false)

function loadReviewed() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      reviewed.value = new Set(JSON.parse(saved))
    } catch {
      reviewed.value = new Set()
    }
  }
}

function persistReviewed() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...reviewed.value]))
}

loadReviewed()

const images = computed(() => batch.value?.images ?? [])
const selected = computed(
  () => images.value.find((img) => img.id === selectedId.value) ?? null,
)

const reviewedCount = computed(() =>
  images.value.filter((img) => reviewed.value.has(img.id)).length,
)

async function loadBatch(batchId) {
  if (!batchId) {
    error.value = 'No batch selected'
    batch.value = null
    selectedId.value = null
    return
  }
  loading.value = true
  error.value = null
  currentBatchId.value = batchId
  progress.value = { done: 0, total: 0 }
  try {
    await pollBatchUntilDone(batchId, { onProgress: (p) => { progress.value = p } })
    batch.value = await getBatchResult(batchId)
    selectedId.value = images.value[0]?.id ?? null
    lastAllReviewed.value = images.value.length > 0 && reviewedCount.value === images.value.length
  } catch (e) {
    error.value = e.message || 'Failed to load batch'
    batch.value = null
    selectedId.value = null
  } finally {
    loading.value = false
  }
}

function selectImage(id) {
  selectedId.value = id
}

function toggleReviewed(id) {
  if (!id) return
  const nowReviewed = !reviewed.value.has(id)
  if (nowReviewed) {
    reviewed.value.add(id)
  } else {
    reviewed.value.delete(id)
  }
  reviewed.value = new Set(reviewed.value)
  persistReviewed()
  if (currentBatchId.value) {
    patchImageReviewed(currentBatchId.value, id, nowReviewed).catch(() => {})
    syncBatchStatus()
  }
}

// Batch status follows review completeness automatically:
// all images reviewed -> "reviewed"; otherwise -> "done". Only PATCHes on change.
function syncBatchStatus() {
  const total = images.value.length
  if (!currentBatchId.value || total === 0) return
  const allReviewed = reviewedCount.value === total
  if (allReviewed === lastAllReviewed.value) return
  lastAllReviewed.value = allReviewed
  patchBatch(currentBatchId.value, {
    status: allReviewed ? 'reviewed' : 'done',
    reviewer: allReviewed ? REVIEWER : null,
  }).catch(() => {})
}

function isReviewed(id) {
  return reviewed.value.has(id)
}

export function useInspection() {
  return {
    batch,
    images,
    selected,
    selectedId,
    hoveredDefectId,
    loading,
    error,
    reviewed,
    reviewedCount,
    currentBatchId,
    progress,
    loadBatch,
    selectImage,
    toggleReviewed,
    isReviewed,
  }
}
