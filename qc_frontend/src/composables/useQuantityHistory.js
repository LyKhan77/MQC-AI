import { ref } from 'vue'
import { deleteQuantityCheck, listQuantityChecks } from '../api/quantity.js'

const checks = ref([])

async function refresh() {
  try {
    checks.value = await listQuantityChecks()
  } catch {
    // keep whatever is loaded if the server is unreachable
  }
}

async function remove(id) {
  await deleteQuantityCheck(id)
  checks.value = checks.value.filter((c) => c.id !== id)
}

export function useQuantityHistory() {
  return { checks, refresh, remove }
}
