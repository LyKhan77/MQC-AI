// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'

import MeasurementStudio from '../MeasurementStudio.vue'


const mocks = vi.hoisted(() => ({
  processMeasurement: vi.fn(),
  saveMeasurementRun: vi.fn(),
  listMeasurementRuns: vi.fn(),
  getMeasurementRun: vi.fn(),
  deleteMeasurementRun: vi.fn(),
  log: vi.fn(),
  showToast: vi.fn(),
}))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (key) => key }) }))
vi.mock('../../composables/useAuditLog.js', () => ({ useAuditLog: () => ({ log: mocks.log }) }))
vi.mock('../../composables/useToast.js', () => ({ useToast: () => ({ showToast: mocks.showToast }) }))
vi.mock('../../composables/useCameras.js', () => ({
  useCameras: () => ({ cameras: ref([{ id: 'cam-1', name: 'QC Top Camera', status: 'online' }]), refresh: vi.fn() }),
}))
vi.mock('../../api/measurements.js', () => ({
  processMeasurement: mocks.processMeasurement,
  saveMeasurementRun: mocks.saveMeasurementRun,
  listMeasurementRuns: mocks.listMeasurementRuns,
  getMeasurementRun: mocks.getMeasurementRun,
  deleteMeasurementRun: mocks.deleteMeasurementRun,
}))

function file(name = 'bracket.png') {
  return new File(['image'], name, { type: 'image/png' })
}

function processed(sourceType = 'image') {
  return {
    source_key: 'tmp-measurement-1',
    source_type: sourceType,
    source_filename: sourceType === 'image' ? 'bracket.png' : 'cam-1.jpg',
    source_camera_id: sourceType === 'image' ? null : 'cam-1',
    frame_url: '/api/measurements/files/tmp-measurement-1/frame.jpg',
    width: 160,
    height: 120,
    calibration: {
      valid: true,
      mm_per_pixel: 0.5,
      point_a: [0, 0],
      point_b: [100, 0],
      known_mm: 50,
    },
    readiness: 'ready',
    reason: '',
    candidates: [{
      points: [[20, 30], [140, 30]],
      length_px: 120,
      angle: 0,
      confidence: 0.95,
      source: 'lsd',
    }],
  }
}

async function stage(wrapper) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: [file()], configurable: true })
  await input.trigger('change')
}

describe('MeasurementStudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listMeasurementRuns.mockResolvedValue([])
    mocks.processMeasurement.mockResolvedValue(processed())
    mocks.saveMeasurementRun.mockResolvedValue({ id: 'measurement-1', name: 'BRKT-001' })
  })

  it('stages an upload without processing it', async () => {
    const wrapper = mount(MeasurementStudio)

    await stage(wrapper)

    expect(wrapper.text()).toContain('bracket.png')
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
  })

  it('processes an uploaded image and renders candidate edges', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({ file: expect.any(File) }))
    expect(wrapper.findAll('.measurement-candidate')).toHaveLength(1)
  })

  it('triggers one Live Camera capture through the same process API', async () => {
    const wrapper = mount(MeasurementStudio)
    mocks.processMeasurement.mockResolvedValueOnce(processed('live'))

    await wrapper.find('.source-live').trigger('click')
    await wrapper.find('.camera-select').setValue('cam-1')
    await wrapper.find('.trigger-capture').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({ cameraId: 'cam-1' }))
    expect(wrapper.text()).toContain('cam-1.jpg')
  })

  it('evaluates a selected edge with editable per-item tolerance', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-candidate').trigger('click')

    await wrapper.find('.item-nominal').setValue('60')
    await wrapper.find('.item-tolerance').setValue('2')
    await wrapper.find('.evaluate-measurement').trigger('click')

    expect(wrapper.find('.measurement-status').text()).toContain('PASS')
    expect(wrapper.find('.measurement-summary').text()).toContain('PASS')
  })

  it('saves the evaluated measurement run', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-candidate').trigger('click')
    await wrapper.find('.item-nominal').setValue('60')
    await wrapper.find('.item-tolerance').setValue('2')
    await wrapper.find('.evaluate-measurement').trigger('click')
    await wrapper.find('.run-name').setValue('BRKT-001')
    await wrapper.find('.save-measurement').trigger('click')
    await flushPromises()

    expect(mocks.saveMeasurementRun).toHaveBeenCalledWith(expect.objectContaining({
      source_key: 'tmp-measurement-1',
      items: expect.arrayContaining([expect.objectContaining({ status: 'PASS' })]),
    }))
    expect(mocks.showToast).toHaveBeenCalled()
  })

  it('filters and reopens a saved measurement from History', async () => {
    mocks.listMeasurementRuns.mockResolvedValueOnce([{
      id: 'measurement-1',
      name: 'BRKT-001',
      source_type: 'image',
      source_filename: 'bracket.png',
      source_url: '/saved/frame.jpg',
      width: 160,
      height: 120,
      calibration: processed().calibration,
      items: [{ id: 'E1', label: 'Edge E1', measured: 60, unit: 'mm', status: 'PASS', points: [[20, 30], [140, 30]] }],
      summary: { status: 'PASS' },
      created_at: '2026-08-10',
    }])
    const wrapper = mount(MeasurementStudio)
    await flushPromises()

    expect(wrapper.findAll('.history-row')).toHaveLength(1)
    await wrapper.find('.history-search').setValue('missing')
    expect(wrapper.findAll('.history-row')).toHaveLength(0)
    await wrapper.find('.history-search').setValue('BRKT')
    await wrapper.find('.history-run').trigger('click')

    expect(wrapper.find('.measurement-item').text()).toContain('PASS')
    expect(wrapper.find('.measurement-image').attributes('src')).toBe('/saved/frame.jpg')
  })
})
