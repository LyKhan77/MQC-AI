import { describe, it, expect, vi, afterEach } from 'vitest'
import { submitBatch, pollBatchUntilDone } from './batches.js'

function fetchSequence(items) {
  let i = 0
  return vi.fn().mockImplementation(() => {
    const r = items[Math.min(i, items.length - 1)]
    i += 1
    return Promise.resolve({ ok: r.status < 300, status: r.status, json: async () => r.body })
  })
}

describe('batches api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('submitBatch maps camelCase to snake_case', async () => {
    const f = fetchSequence([{ status: 201, body: { batch_id: 'b1', job_id: 'j1' } }])
    vi.stubGlobal('fetch', f)
    const res = await submitBatch({ batchName: 'S1', sourcePath: '/crops', cameraId: 'cam-01' })
    expect(f).toHaveBeenCalledWith('/api/batches', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ batch_name: 'S1', source_path: '/crops', camera_id: 'cam-01' }),
    })
    expect(res.batch_id).toBe('b1')
  })

  it('pollBatchUntilDone resolves on done and reports progress', async () => {
    vi.stubGlobal('fetch', fetchSequence([
      { status: 200, body: { batch_id: 'b1', status: 'done', progress: { done: 3, total: 3 } } },
    ]))
    const seen = []
    const res = await pollBatchUntilDone('b1', { onProgress: (p) => seen.push(p), intervalMs: 0 })
    expect(res.status).toBe('done')
    expect(seen).toEqual([{ done: 3, total: 3 }])
  })

  it('pollBatchUntilDone throws on failed', async () => {
    vi.stubGlobal('fetch', fetchSequence([
      { status: 200, body: { batch_id: 'b1', status: 'failed', progress: { done: 0, total: 0 } } },
    ]))
    await expect(pollBatchUntilDone('b1', { intervalMs: 0 })).rejects.toThrow(/failed/i)
  })

  it('listBatches maps snake_case to the frontend shape', async () => {
    vi.stubGlobal('fetch', fetchSequence([{
      status: 200,
      body: [{
        id: 'batch_1', name: 'Shift 1', source_path: '/crops', camera_id: 'cam-01',
        created_at: '2026-06-27T08:00:00', image_count: 3, defect_count: 2,
        status: 'done', reviewer: null, model_info: { detection: 'YOLOv8n' },
        reviewed_count: 1,
      }],
    }]))
    const { listBatches } = await import('./batches.js')
    const rows = await listBatches()
    expect(rows[0]).toEqual({
      id: 'batch_1', name: 'Shift 1', sourcePath: '/crops', cameraId: 'cam-01',
      cameraName: 'cam-01', createdAt: '2026-06-27T08:00:00', imageCount: 3,
      defectCount: 2, status: 'done', reviewer: null, modelInfo: { detection: 'YOLOv8n' },
      reviewedCount: 1,
    })
  })

  it('patchBatch sends status + reviewer', async () => {
    const f = fetchSequence([{ status: 200, body: { id: 'b1', status: 'reviewed' } }])
    vi.stubGlobal('fetch', f)
    const { patchBatch } = await import('./batches.js')
    await patchBatch('b1', { status: 'reviewed', reviewer: 'inspector@gspemail.com' })
    expect(f).toHaveBeenCalledWith('/api/batches/b1', {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: 'reviewed', reviewer: 'inspector@gspemail.com' }),
    })
  })

  it('pollBatchUntilDone throws after maxAttempts', async () => {
    vi.stubGlobal('fetch', fetchSequence([
      { status: 200, body: { batch_id: 'b1', status: 'processing', progress: { done: 0, total: 3 } } },
    ]))
    const { pollBatchUntilDone } = await import('./batches.js')
    await expect(
      pollBatchUntilDone('b1', { intervalMs: 0, maxAttempts: 2 }),
    ).rejects.toThrow(/timed out/i)
  })
})
