import { ref } from 'vue'
import {
  listCameras,
  createCamera,
  updateCamera as apiUpdateCamera,
  deleteCamera as apiDeleteCamera,
} from '../api/cameras.js'

const cameras = ref([])

async function refresh() {
  try {
    cameras.value = await listCameras()
  } catch {
    // keep current list if the server is unreachable
  }
}

async function addCamera(cam) {
  const id = `cam-${String(Date.now()).slice(-6)}`
  await createCamera({ ...cam, id })
  await refresh()
  return id
}

async function updateCamera(id, patch) {
  await apiUpdateCamera(id, patch)
  await refresh()
}

async function deleteCamera(id) {
  await apiDeleteCamera(id)
  await refresh()
}

function getById(id) {
  return cameras.value.find((c) => c.id === id)
}

refresh()

export function useCameras() {
  return { cameras, refresh, addCamera, updateCamera, deleteCamera, getById }
}
