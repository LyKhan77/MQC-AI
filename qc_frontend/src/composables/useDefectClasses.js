import { ref } from 'vue'
import {
  listDefectClasses,
  createDefectClass,
  updateDefectClass,
  deleteDefectClass,
} from '../api/defectClasses.js'

const classes = ref([])

async function refresh() {
  try {
    classes.value = await listDefectClasses()
  } catch {
    // keep current state if the server is unreachable
  }
}

async function add(payload) {
  const created = await createDefectClass(payload)
  classes.value = [...classes.value, created]
  return created
}

async function update(id, patch) {
  const updated = await updateDefectClass(id, patch)
  classes.value = classes.value.map((c) => (c.id === id ? updated : c))
  return updated
}

async function toggle(cls) {
  return update(cls.id, { enabled: !cls.enabled })
}

async function remove(id) {
  await deleteDefectClass(id)
  classes.value = classes.value.filter((c) => c.id !== id)
}

export function useDefectClasses() {
  return { classes, refresh, add, update, toggle, remove }
}
