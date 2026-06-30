import { ref, computed } from 'vue'
import {
  pollBatchUntilDone,
  getBatchResult,
  getBatchStatus,
  runBatch,
  patchImageReviewed,
  patchBatch,
  deleteImage,
} from '../api/batches.js'

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
const needsRun = ref(false)

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

// Decide how to open a batch: a "pending" batch waits for an explicit run
// (the QC Studio confirmation step) and must NOT be polled; anything already
// processing/done/reviewed is loaded and displayed normally.
async function prepareBatch(batchId) {
  if (!batchId) {
    error.value = 'No batch selected'
    batch.value = null
    selectedId.value = null
    needsRun.value = false
    return
  }
  error.value = null
  currentBatchId.value = batchId
  try {
    const status = await getBatchStatus(batchId)
    if (status.status === 'pending') {
      needsRun.value = true
      batch.value = await getBatchResult(batchId)
      selectedId.value = images.value[0]?.id ?? null
      return
    }
  } catch {
    // fall through; loadBatch will surface a clearer error
  }
  needsRun.value = false
  await loadBatch(batchId)
}

// Start segmentation for a pending batch (optional per-run confidence
// override), then poll + display the results.
async function runAndLoad(batchId, confidenceThreshold) {
  if (!batchId) return
  needsRun.value = false
  try {
    await runBatch(batchId, { confidenceThreshold })
  } catch (e) {
    error.value = e.message || 'Failed to start segmentation'
    needsRun.value = true
    return
  }
  await loadBatch(batchId)
}

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
    // Reconcile on open: a batch already fully reviewed should read as "reviewed".
    if (lastAllReviewed.value) {
      patchBatch(batchId, { status: 'reviewed', reviewer: REVIEWER }).catch(() => {})
    }
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

async function removeImage(imageId) {
  if (!imageId || !currentBatchId.value) return
  await deleteImage(currentBatchId.value, imageId)
  if (batch.value) {
    batch.value = {
      ...batch.value,
      images: images.value.filter((img) => img.id !== imageId),
    }
  }
  if (selectedId.value === imageId) {
    selectedId.value = images.value[0]?.id ?? null
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
    needsRun,
    prepareBatch,
    runAndLoad,
    loadBatch,
    removeImage,
    selectImage,
    toggleReviewed,
    isReviewed,
  }
}
