import { ref } from 'vue'
import { listQuantityChecks } from '../api/quantity.js'

const checks = ref([])

async function refresh() {
  try {
    checks.value = await listQuantityChecks()
  } catch {
    // keep whatever is loaded if the server is unreachable
  }
}

export function useQuantityHistory() {
  return { checks, refresh }
}
