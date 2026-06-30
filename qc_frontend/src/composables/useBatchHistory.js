import { ref } from 'vue'
import { listBatches, deleteBatch } from '../api/batches.js'

const batches = ref([])

async function refresh() {
  try {
    batches.value = await listBatches()
  } catch {
    // keep whatever is loaded if the server is unreachable
  }
}

async function remove(id) {
  await deleteBatch(id)
  batches.value = batches.value.filter((b) => b.id !== id)
}

export function useBatchHistory() {
  return { batches, refresh, remove }
}
