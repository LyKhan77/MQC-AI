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

export function mapBatchSummary(s) {
  return {
    id: s.id,
    name: s.name,
    sourcePath: s.source_path,
    cameraId: s.camera_id,
    cameraName: s.camera_id ?? '',
    createdAt: s.created_at,
    imageCount: s.image_count,
    defectCount: s.defect_count,
    status: s.status,
    reviewer: s.reviewer,
    modelInfo: s.model_info ?? {},
  }
}

export async function listBatches() {
  const data = await apiGet('/batches')
  return data.map(mapBatchSummary)
}

export function patchImageReviewed(batchId, imageId, reviewed) {
  return apiPatch(`/batches/${batchId}/images/${imageId}`, { reviewed })
}

export async function pollBatchUntilDone(batchId, { onProgress, intervalMs = 1000, maxAttempts = 600 } = {}) {
  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const status = await getBatchStatus(batchId)
    if (onProgress) onProgress(status.progress)
    if (status.status === 'done' || status.status === 'reviewed') return status
    if (status.status === 'failed') throw new Error('Batch processing failed')
    await new Promise((r) => setTimeout(r, intervalMs))
  }
  throw new Error('Batch polling timed out')
}
