import { apiPost } from './client.js'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function detectInspection({ file, cameraId, cropMode = 'full' }) {
  const fd = new FormData()
  if (file) fd.append('file', file)
  if (cameraId) fd.append('camera_id', cameraId)
  fd.append('crop_mode', cropMode)
  const res = await fetch(`${BASE}/inspection/detect`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function inspectionToQc(keys) {
  return apiPost('/inspection/to-qc', { keys })
}
