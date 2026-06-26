import { apiGet, apiPost, apiPatch } from './client.js'

export function submitBatch({ batchName, sourcePath, cameraId }) {
  return apiPost('/batches', {
    batch_name: batchName,
    source_path: sourcePath,
    camera_id: cameraId ?? null,
  })
}

export function getBatchStatus(batchId) {
  return apiGet(`/batches/${batchId}/status`)
}

export function getBatchResult(batchId) {
  return apiGet(`/batches/${batchId}`)
}

export function patchImageReviewed(batchId, imageId, reviewed) {
  return apiPatch(`/batches/${batchId}/images/${imageId}`, { reviewed })
}

export async function pollBatchUntilDone(batchId, { onProgress, intervalMs = 1000 } = {}) {
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const status = await getBatchStatus(batchId)
    if (onProgress) onProgress(status.progress)
    if (status.status === 'done' || status.status === 'reviewed') return status
    if (status.status === 'failed') throw new Error('Batch processing failed')
    await new Promise((r) => setTimeout(r, intervalMs))
  }
}
