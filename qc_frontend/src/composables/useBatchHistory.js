import { ref } from 'vue'
import { listBatches } from '../api/batches.js'

const batches = ref([])

async function refresh() {
  try {
    batches.value = await listBatches()
  } catch {
    // keep whatever is loaded if the server is unreachable
  }
}

export function useBatchHistory() {
  return { batches, refresh }
}
