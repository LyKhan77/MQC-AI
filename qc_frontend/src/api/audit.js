import { apiGet, apiPost } from './client.js'

export function postAudit({ user, action, detail }) {
  return apiPost('/audit', { user, action, detail })
}

export function listAudit() {
  return apiGet('/audit')
}
