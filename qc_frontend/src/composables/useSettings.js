import { ref } from 'vue'
import { MOCK } from '../utils/mockData.js'

const STORAGE_KEY = 'mqc-settings'

const defaults = {
  confidenceThreshold: MOCK.settings.confidenceThreshold,
  detectionModel: MOCK.settings.detectionModel,
  segmentationModel: MOCK.settings.segmentationModel,
}

const settings = ref({ ...defaults })

function load() {
  const saved = localStorage.getItem(STORAGE_KEY)
  if (saved) {
    try {
      settings.value = { ...defaults, ...JSON.parse(saved) }
    } catch {
      // keep defaults
    }
  }
}

load()

function update(patch) {
  settings.value = { ...settings.value, ...patch }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings.value))
}

export function useSettings() {
  return { settings, update }
}
