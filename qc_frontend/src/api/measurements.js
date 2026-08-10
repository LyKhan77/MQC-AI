import { apiDelete, apiGet, apiPost } from './client.js'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function processMeasurement({ file, cameraId, sourceType = 'image', calibration, options = {} }) {
  const fd = new FormData()
  if (file) fd.append('file', file)
  if (cameraId) fd.append('camera_id', cameraId)
  if (file) fd.append('source_type', sourceType)
  fd.append('calibration', JSON.stringify(calibration || {}))
  fd.append('options', JSON.stringify(options))
  const response = await fetch(`${BASE}/measurements/process`, { method: 'POST', body: fd })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export function saveMeasurementRun(payload) {
  return apiPost('/measurements', payload)
}

export function listMeasurementRuns() {
  return apiGet('/measurements')
}

export function getMeasurementRun(id) {
  return apiGet(`/measurements/${id}`)
}

export function deleteMeasurementRun(id) {
  return apiDelete(`/measurements/${id}`)
}
