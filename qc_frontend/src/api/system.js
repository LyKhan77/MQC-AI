import { apiGet } from './client.js'

export function listGpus() {
  return apiGet('/system/gpus')
}
