import { ref, computed } from 'vue'
import { MOCK } from '../utils/mockData.js'

const STORAGE_KEY = 'mqc-batch-history'
const batches = ref([])

function load() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      batches.value = JSON.parse(saved)
      return
    } catch {
      // fallthrough
    }
  }
  batches.value = [...MOCK.batchHistory]
  persist()
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(batches.value))
}

load()

function addBatch(batch) {
  const id = `batch-${String(Date.now()).slice(-6)}`
  const entry = {
    id,
    status: 'pending',
    reviewer: null,
    createdAt: new Date().toISOString(),
    ...batch,
  }
  batches.value.unshift(entry)
  persist()
  return id
}

function updateBatch(id, patch) {
  const idx = batches.value.findIndex((b) => b.id === id)
  if (idx !== -1) {
    batches.value[idx] = { ...batches.value[idx], ...patch }
    persist()
  }
}

function getById(id) {
  return batches.value.find((b) => b.id === id)
}

const pendingCount = computed(() => batches.value.filter((b) => b.status === 'pending').length)

export function useBatchHistory() {
  return { batches, addBatch, updateBatch, getById, pendingCount }
}
