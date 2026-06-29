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
