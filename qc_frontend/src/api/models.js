import { apiGet } from './client.js'

export function listModels() {
  return apiGet('/models')
}
