import { apiGet, apiPost, apiPatch, apiDelete } from './client.js'

export function listDefectClasses() {
  return apiGet('/defect-classes')
}

export function createDefectClass(payload) {
  return apiPost('/defect-classes', payload)
}

export function updateDefectClass(id, patch) {
  return apiPatch(`/defect-classes/${id}`, patch)
}

export function deleteDefectClass(id) {
  return apiDelete(`/defect-classes/${id}`)
}
