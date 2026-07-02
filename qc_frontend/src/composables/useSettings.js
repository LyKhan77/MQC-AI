import { ref } from 'vue'
import { getSettings, updateSettings } from '../api/settings.js'

const settings = ref({
  confidenceThreshold: 0.5,
  qcConfidenceThreshold: 0.5,
  detectionModel: 'YOLOv8n',
  segmentationModel: 'SAM3',
  defectStrategy: 'mock',
  activeModel: '',
  inputModeEnabled: true,
  quantityModel: '',
  quantityConfidenceThreshold: 0.5,
  quantityNmsIou: 0.45,
  quantityAgnosticNms: true,
})

async function refresh() {
  try {
    settings.value = await getSettings()
  } catch {
    // keep defaults if the server is unreachable
  }
}

async function update(patch) {
  settings.value = { ...settings.value, ...patch }
  await updateSettings(patch)
}

refresh()

export function useSettings() {
  return { settings, refresh, update }
}
