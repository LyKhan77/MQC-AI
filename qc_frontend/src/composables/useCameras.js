import { ref } from 'vue'
import { MOCK } from '../utils/mockData.js'

const STORAGE_KEY = 'mqc-cameras'
const cameras = ref([])

function load() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      cameras.value = JSON.parse(saved)
      return
    } catch {
      // fallthrough to seed
    }
  }
  cameras.value = [...MOCK.cameras]
  persist()
}

function persist() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cameras.value))
}

load()

function addCamera(cam) {
  const id = `cam-${String(Date.now()).slice(-6)}`
  cameras.value.push({ ...cam, id })
  persist()
  return id
}

function updateCamera(id, patch) {
  const idx = cameras.value.findIndex((c) => c.id === id)
  if (idx !== -1) {
    cameras.value[idx] = { ...cameras.value[idx], ...patch }
    persist()
  }
}

function deleteCamera(id) {
  cameras.value = cameras.value.filter((c) => c.id !== id)
  persist()
}

function getById(id) {
  return cameras.value.find((c) => c.id === id)
}

export function useCameras() {
  return { cameras, addCamera, updateCamera, deleteCamera, getById }
}
