import { apiGet, apiPost, apiPatch, apiDelete } from './client.js'

export function listCameras() {
  return apiGet('/cameras')
}

export function createCamera(camera) {
  return apiPost('/cameras', camera)
}

export function updateCamera(id, patch) {
  return apiPatch(`/cameras/${id}`, patch)
}

export function deleteCamera(id) {
  return apiDelete(`/cameras/${id}`)
}

export function finalizeCropSession(id) {
  return apiPost(`/cameras/${id}/crop-session/finalize`, {})
}

export function startCropSession(id) {
  return apiPost(`/cameras/${id}/crop-session/start`, {})
}

export function captureDetection(id) {
  return apiPost(`/cameras/${id}/capture`, {})
}

export function approveCrops(id, files) {
  return apiPost(`/cameras/${id}/crop-session/approve`, { files })
}
