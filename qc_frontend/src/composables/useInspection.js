import { ref, computed } from 'vue'

const STORAGE_KEY = 'mqc-reviewed'

const batch = ref(null)
const selectedId = ref(null)
const hoveredDefectId = ref(null)
const loading = ref(false)
const error = ref(null)
const reviewed = ref(new Set())

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

async function loadBatch(url = '/mock/batch-shift1.json') {
  loading.value = true
  error.value = null
  try {
    // Simulate network delay for realistic UX
    await new Promise((r) => setTimeout(r, 1200))
    const res = await fetch(url)
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    batch.value = await res.json()
    selectedId.value = images.value[0]?.id ?? null
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
  if (reviewed.value.has(id)) {
    reviewed.value.delete(id)
  } else {
    reviewed.value.add(id)
  }
  reviewed.value = new Set(reviewed.value)
  persistReviewed()
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
    loadBatch,
    selectImage,
    toggleReviewed,
    isReviewed,
  }
}
