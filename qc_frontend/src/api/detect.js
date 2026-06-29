const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function detectImage(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/detect/image`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function uploadVideo(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/detect/video`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export const videoStreamUrl = (id) => `${BASE}/detect/video/${id}/stream`

export async function processImage(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/detect/image/process`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function extractVideo(videoId) {
  const res = await fetch(`${BASE}/detect/video/${videoId}/extract`, { method: 'POST' })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function videoExtractStatus(videoId) {
  const res = await fetch(`${BASE}/detect/video/${videoId}/extract/status`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function listDetectCrops(key) {
  const res = await fetch(`${BASE}/detect/crop-session/${key}`)
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export async function approveDetectCrops(key, files) {
  const res = await fetch(`${BASE}/detect/crop-session/${key}/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files }),
  })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}
