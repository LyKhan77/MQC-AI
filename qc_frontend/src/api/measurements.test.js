import { describe, it, expect, vi, afterEach } from 'vitest'

import {
  deleteMeasurementRun,
  getMeasurementRun,
  listMeasurementRuns,
  processMeasurement,
  saveMeasurementRun,
} from './measurements.js'


function ok(body) {
  return vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => body })
}


describe('measurements api', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('processes an uploaded image as multipart form data', async () => {
    const fetchMock = ok({ source_type: 'image' })
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['image'], 'sample.png', { type: 'image/png' })

    await processMeasurement({
      file,
      calibration: { point_a: [0, 0], point_b: [10, 0], known_mm: 5 },
    })

    const [path, options] = fetchMock.mock.calls[0]
    expect(path).toBe('/api/measurements/process')
    expect(options.method).toBe('POST')
    expect(options.body).toBeInstanceOf(FormData)
    expect(options.body.get('file')).toBe(file)
    expect(JSON.parse(options.body.get('calibration')).known_mm).toBe(5)
  })

  it('processes a Live Camera frame by camera id', async () => {
    const fetchMock = ok({ source_type: 'live_camera' })
    vi.stubGlobal('fetch', fetchMock)

    await processMeasurement({
      cameraId: 'cam-1',
      calibration: { point_a: [0, 0], point_b: [10, 0], known_mm: 5 },
    })

    const body = fetchMock.mock.calls[0][1].body
    expect(body.get('camera_id')).toBe('cam-1')
    expect(body.get('file')).toBeNull()
  })

  it('uses measurement run CRUD endpoints', async () => {
    const fetchMock = ok({ id: 'measurement-1' })
    vi.stubGlobal('fetch', fetchMock)

    await saveMeasurementRun({ name: 'BRKT-001' })
    await listMeasurementRuns()
    await getMeasurementRun('measurement-1')
    await deleteMeasurementRun('measurement-1')

    expect(fetchMock.mock.calls.map(([path, options]) => `${options.method} ${path}`)).toEqual([
      'POST /api/measurements',
      'GET /api/measurements',
      'GET /api/measurements/measurement-1',
      'DELETE /api/measurements/measurement-1',
    ])
  })
})
