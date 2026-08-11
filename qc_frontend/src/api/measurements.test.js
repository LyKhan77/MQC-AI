import { describe, it, expect, vi, afterEach } from 'vitest'

import {
  captureMeasurement,
  createMeasurementProfile,
  createMeasurementSession,
  deleteMeasurementRun,
  deleteMeasurementProfile,
  deleteMeasurementSession,
  deleteMeasurementView,
  getMeasurementSession,
  getMeasurementRun,
  listMeasurementProfiles,
  listMeasurementSessions,
  listMeasurementRuns,
  processMeasurement,
  saveMeasurementRun,
  saveMeasurementView,
  updateMeasurementProfile,
  updateMeasurementSession,
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

  it('sends the proper task and view type with the process request', async () => {
    const fetchMock = ok({ source_type: 'image' })
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['image'], 'holes.png', { type: 'image/png' })

    await processMeasurement({
      file,
      taskType: 'hole_diameter',
      viewType: 'top',
      calibration: { point_a: [0, 0], point_b: [10, 0], known_mm: 5 },
    })

    const body = fetchMock.mock.calls[0][1].body
    expect(body.get('task_type')).toBe('hole_diameter')
    expect(body.get('view_type')).toBe('top')
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

  it('captures a Live Camera frame without running measurement', async () => {
    const fetchMock = ok({ source_key: 'tmp-live-capture', source_type: 'live_camera' })
    vi.stubGlobal('fetch', fetchMock)

    await captureMeasurement({ cameraId: 'cam-1' })

    const [path, options] = fetchMock.mock.calls[0]
    expect(path).toBe('/api/measurements/capture')
    expect(options.method).toBe('POST')
    expect(options.body.get('camera_id')).toBe('cam-1')
  })

  it('processes a staged Live Camera frame by source key after calibration', async () => {
    const fetchMock = ok({ source_type: 'live_camera' })
    vi.stubGlobal('fetch', fetchMock)

    await processMeasurement({
      sourceKey: 'tmp-live-capture',
      sourceFilename: 'cam-1.jpg',
      sourceCameraId: 'cam-1',
      sourceType: 'live_camera',
      calibration: { point_a: [0, 0], point_b: [100, 0], known_mm: 50 },
    })

    const body = fetchMock.mock.calls[0][1].body
    expect(body.get('source_key')).toBe('tmp-live-capture')
    expect(body.get('source_filename')).toBe('cam-1.jpg')
    expect(body.get('source_camera_id')).toBe('cam-1')
    expect(body.get('source_type')).toBe('live_camera')
  })

  it('preserves Mobile Camera as the client capture source', async () => {
    const fetchMock = ok({ source_type: 'mobile_camera' })
    vi.stubGlobal('fetch', fetchMock)
    const file = new File(['image'], 'mobile.jpg', { type: 'image/jpeg' })

    await processMeasurement({
      file,
      sourceType: 'mobile_camera',
      calibration: { point_a: [0, 0], point_b: [10, 0], known_mm: 5 },
    })

    expect(fetchMock.mock.calls[0][1].body.get('source_type')).toBe('mobile_camera')
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

  it('uses measurement profile and session endpoints', async () => {
    const fetchMock = ok({ id: 'measurement-1', views: [] })
    vi.stubGlobal('fetch', fetchMock)

    await createMeasurementProfile({ name: 'Global' })
    await listMeasurementProfiles()
    await updateMeasurementProfile('profile-1', { status: 'valid' })
    await deleteMeasurementProfile('profile-1')
    await createMeasurementSession('BRKT-001')
    await listMeasurementSessions()
    await getMeasurementSession('session-1')
    await updateMeasurementSession('session-1', { status: 'complete' })
    await saveMeasurementView('session-1', { source_key: 'tmp-1' })
    await deleteMeasurementView('session-1', 'view-1')
    await deleteMeasurementSession('session-1')

    expect(fetchMock.mock.calls.map(([path, options]) => `${options.method} ${path}`)).toEqual([
      'POST /api/measurement-profiles',
      'GET /api/measurement-profiles',
      'PATCH /api/measurement-profiles/profile-1',
      'DELETE /api/measurement-profiles/profile-1',
      'POST /api/measurement-sessions',
      'GET /api/measurement-sessions',
      'GET /api/measurement-sessions/session-1',
      'PATCH /api/measurement-sessions/session-1',
      'POST /api/measurement-sessions/session-1/views',
      'DELETE /api/measurement-sessions/session-1/views/view-1',
      'DELETE /api/measurement-sessions/session-1',
    ])
    expect(fetchMock.mock.calls[0][1].body).toBe(JSON.stringify({ name: 'Global' }))
    expect(fetchMock.mock.calls[7][1].body).toBe(JSON.stringify({ status: 'complete' }))
    expect(fetchMock.mock.calls[8][1].body).toBe(JSON.stringify({ source_key: 'tmp-1' }))
  })
})
