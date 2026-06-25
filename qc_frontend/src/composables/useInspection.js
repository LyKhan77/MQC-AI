import { ref, computed } from 'vue'

// Shared singleton state (module scope) — ponytail: cukup untuk 1 studio aktif, no Pinia.
const batch = ref(null)
const selectedId = ref(null)
const hoveredDefectId = ref(null)

const images = computed(() => batch.value?.images ?? [])
const selected = computed(
  () => images.value.find((img) => img.id === selectedId.value) ?? null,
)

async function loadBatch(url = '/mock/batch-shift1.json') {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Gagal load batch: ${res.status}`)
  batch.value = await res.json()
  selectedId.value = images.value[0]?.id ?? null
}

function selectImage(id) {
  selectedId.value = id
}

export function useInspection() {
  return { batch, images, selected, selectedId, hoveredDefectId, loadBatch, selectImage }
}
