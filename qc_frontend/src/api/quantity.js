import { apiDelete, apiGet, apiPost } from './client.js'

const BASE = import.meta.env.VITE_API_BASE ?? '/api'

export async function detectQuantityImage(file) {
  const fd = new FormData()
  fd.append('file', file)
  const res = await fetch(`${BASE}/quantity/detect/image`, { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

export function createQuantityCheck(payload) {
  return apiPost('/quantity/checks', payload)
}

export function listQuantityChecks() {
  return apiGet('/quantity/checks')
}

export function deleteQuantityCheck(id) {
  return apiDelete(`/quantity/checks/${id}`)
}
