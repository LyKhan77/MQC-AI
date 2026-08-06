import { apiPost } from './client.js'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function detectInspection({ file, cameraId, cropMode = 'full', debugCrop = false, maskPolygon }) {
  const fd = new FormData()
  if (file) fd.append('file', file)
  if (cameraId) fd.append('camera_id', cameraId)
  fd.append('crop_mode', cropMode)
  fd.append('debug_crop', String(debugCrop))
  if (maskPolygon?.length) fd.append('mask_polygon', JSON.stringify(maskPolygon))
  const res = await fetch(`${BASE}/inspection/detect`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function previewAutocrop(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/inspection/autocrop-preview`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function inspectionToQc(captures) {
  return apiPost('/inspection/to-qc', { captures })
}
