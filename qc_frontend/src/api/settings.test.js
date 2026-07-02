import { describe, it, expect, vi, afterEach } from 'vitest'
import { getSettings, updateSettings } from './settings.js'

function ok(body) {
  return vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => body })
}

describe('settings api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('getSettings maps snake_case to camelCase', async () => {
    vi.stubGlobal(
      'fetch',
      ok({
        confidence_threshold: 0.7,
        qc_confidence_threshold: 0.4,
        detection_model: 'YOLOv8n',
        segmentation_model: 'SAM3',
        defect_strategy: 'mock',
      }),
    )
    const s = await getSettings()
    expect(s).toMatchObject({
      confidenceThreshold: 0.7,
      qcConfidenceThreshold: 0.4,
      detectionModel: 'YOLOv8n',
      segmentationModel: 'SAM3',
      defectStrategy: 'mock',
    })
  })

  it('updateSettings maps camelCase to snake_case and coerces the threshold', async () => {
    const f = ok({
      confidence_threshold: 0.8,
      detection_model: 'YOLOv8n',
      segmentation_model: 'SAM3',
      defect_strategy: 'sam3_prompt',
    })
    vi.stubGlobal('fetch', f)
    await updateSettings({ confidenceThreshold: '0.8', defectStrategy: 'sam3_prompt' })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ confidence_threshold: 0.8, defect_strategy: 'sam3_prompt' }),
    })
  })

  it('maps qc_model to qcModel and back', async () => {
    vi.stubGlobal('fetch', ok({ qc_model: 'sam3.pt' }))
    const s = await getSettings()
    expect(s.qcModel).toBe('sam3.pt')

    const f = ok({ qc_model: 'sam3.pt' })
    vi.stubGlobal('fetch', f)
    await updateSettings({ qcModel: 'sam3.pt' })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qc_model: 'sam3.pt' }),
    })
  })

  it('maps qc_confidence_threshold to qcConfidenceThreshold and back', async () => {
    vi.stubGlobal('fetch', ok({ qc_confidence_threshold: 0.35 }))
    const s = await getSettings()
    expect(s.qcConfidenceThreshold).toBe(0.35)

    const f = ok({ qc_confidence_threshold: 0.35 })
    vi.stubGlobal('fetch', f)
    await updateSettings({ qcConfidenceThreshold: '0.35' })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ qc_confidence_threshold: 0.35 }),
    })
  })

  it('maps quantity model + confidence both directions', async () => {
    const f = ok({ quantity_model: 'count.pt', quantity_confidence_threshold: 0.6 })
    vi.stubGlobal('fetch', f)
    await updateSettings({ quantityModel: 'count.pt', quantityConfidenceThreshold: '0.6' })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity_model: 'count.pt', quantity_confidence_threshold: 0.6 }),
    })
  })

  it('maps quantity NMS iou + agnostic both directions', async () => {
    const f = ok({ quantity_nms_iou: 0.4, quantity_agnostic_nms: false })
    vi.stubGlobal('fetch', f)
    await updateSettings({ quantityNmsIou: '0.4', quantityAgnosticNms: false })
    expect(f).toHaveBeenCalledWith('/api/settings', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity_nms_iou: 0.4, quantity_agnostic_nms: false }),
    })
  })
})
