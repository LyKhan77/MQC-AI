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
        detection_model: 'YOLOv8n',
        segmentation_model: 'SAM3',
        defect_strategy: 'mock',
      }),
    )
    const s = await getSettings()
    expect(s).toEqual({
      confidenceThreshold: 0.7,
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
})
