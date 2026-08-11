import { afterEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  createMeasurementSession: vi.fn(),
  listMeasurementProfiles: vi.fn(),
  saveMeasurementView: vi.fn(),
  updateMeasurementSession: vi.fn(),
  getMeasurementSession: vi.fn(),
}))

vi.mock('../../api/measurements.js', () => api)

import { useMeasurementSession } from '../useMeasurementSession.js'

function file(name) {
  return new File(['image'], name, { type: 'image/png' })
}

describe('useMeasurementSession', () => {
  afterEach(() => {
    useMeasurementSession().clearSession()
    vi.clearAllMocks()
  })

  it('stages multiple files as separate views and selects newest view', () => {
    const session = useMeasurementSession()

    const views = session.stageImage([file('top.png'), file('reverse.png')])

    expect(views).toHaveLength(2)
    expect(session.views.value).toHaveLength(2)
    expect(session.selectedView.value.sourceFilename).toBe('reverse.png')
    expect(session.views.value.map((view) => view.sourceType)).toEqual(['image', 'image'])
  })

  it('removes a staged view and revokes its local URL', () => {
    const revoke = vi.spyOn(URL, 'revokeObjectURL')
    const session = useMeasurementSession()
    const [view] = session.stageImage(file('top.png'))

    session.removeStagedView(view.id)

    expect(session.views.value).toHaveLength(0)
    expect(revoke).toHaveBeenCalledWith(view.previewUrl)
    revoke.mockRestore()
  })

  it('preserves Live and Mobile source metadata', () => {
    const session = useMeasurementSession()
    const live = session.stageServerCapture({
      source_key: 'tmp-live',
      source_type: 'live_camera',
      source_filename: 'cam-1.jpg',
      source_camera_id: 'cam-1',
      frame_url: '/api/measurements/files/tmp-live/frame.jpg',
      width: 2560,
      height: 1440,
    })
    const mobile = session.stageMobileCapture(file('mobile.jpg'))

    expect(live.sourceType).toBe('live_camera')
    expect(live.sourceKey).toBe('tmp-live')
    expect(live.width).toBe(2560)
    expect(mobile.sourceType).toBe('mobile_camera')
    expect(mobile.sourceFilename).toBe('mobile.jpg')
  })
})
