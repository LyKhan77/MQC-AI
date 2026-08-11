import { apiDelete, apiGet, apiPatch, apiPost } from './client.js'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function captureMeasurement({ cameraId }) {
  const fd = new FormData()
  fd.append('camera_id', cameraId)
  const response = await fetch(`${BASE}/measurements/capture`, { method: 'POST', body: fd })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}

export async function processMeasurement({ file, cameraId, sourceKey, sourceFilename, sourceCameraId, sourceType = 'image', calibration, options = {}, taskType = 'linear_dimension', viewType = 'top' }) {
  const fd = new FormData()
  if (file) fd.append('file', file)
  if (cameraId) fd.append('camera_id', cameraId)
  if (sourceKey) fd.append('source_key', sourceKey)
  if (sourceFilename) fd.append('source_filename', sourceFilename)
  if (sourceCameraId) fd.append('source_camera_id', sourceCameraId)
  if (file || sourceKey) fd.append('source_type', sourceType)
  fd.append('task_type', taskType)
  fd.append('view_type', viewType)
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

export function createMeasurementProfile(payload) {
  return apiPost('/measurement-profiles', payload)
}

export function listMeasurementProfiles() {
  return apiGet('/measurement-profiles')
}

export function updateMeasurementProfile(id, patch) {
  return apiPatch(`/measurement-profiles/${id}`, patch)
}

export function deleteMeasurementProfile(id) {
  return apiDelete(`/measurement-profiles/${id}`)
}

export function createMeasurementSession(name) {
  return apiPost('/measurement-sessions', { name })
}

export function listMeasurementSessions() {
  return apiGet('/measurement-sessions')
}

export function getMeasurementSession(id) {
  return apiGet(`/measurement-sessions/${id}`)
}

export function updateMeasurementSession(id, patch) {
  return apiPatch(`/measurement-sessions/${id}`, patch)
}

export function saveMeasurementView(sessionId, payload) {
  return apiPost(`/measurement-sessions/${sessionId}/views`, payload)
}

export function deleteMeasurementView(sessionId, viewId) {
  return apiDelete(`/measurement-sessions/${sessionId}/views/${viewId}`)
}

export function deleteMeasurementSession(id) {
  return apiDelete(`/measurement-sessions/${id}`)
}
