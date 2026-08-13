// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { ref } from 'vue'

import MeasurementStudio from '../MeasurementStudio.vue'


const mocks = vi.hoisted(() => ({
  captureMeasurement: vi.fn(),
  detectMeasurementJig: vi.fn(),
  processMeasurement: vi.fn(),
  saveMeasurementRun: vi.fn(),
  listMeasurementRuns: vi.fn(),
  getMeasurementRun: vi.fn(),
  deleteMeasurementRun: vi.fn(),
  createMeasurementSession: vi.fn(),
  listMeasurementProfiles: vi.fn(),
  saveMeasurementView: vi.fn(),
  updateMeasurementSession: vi.fn(),
  getMeasurementSession: vi.fn(),
  listMeasurementSessions: vi.fn(),
  deleteMeasurementSession: vi.fn(),
  deleteMeasurementView: vi.fn(),
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
  captureMeasurement: mocks.captureMeasurement,
  detectMeasurementJig: mocks.detectMeasurementJig,
  processMeasurement: mocks.processMeasurement,
  saveMeasurementRun: mocks.saveMeasurementRun,
  listMeasurementRuns: mocks.listMeasurementRuns,
  getMeasurementRun: mocks.getMeasurementRun,
  deleteMeasurementRun: mocks.deleteMeasurementRun,
  createMeasurementSession: mocks.createMeasurementSession,
  listMeasurementProfiles: mocks.listMeasurementProfiles,
  saveMeasurementView: mocks.saveMeasurementView,
  updateMeasurementSession: mocks.updateMeasurementSession,
  getMeasurementSession: mocks.getMeasurementSession,
  listMeasurementSessions: mocks.listMeasurementSessions,
  deleteMeasurementSession: mocks.deleteMeasurementSession,
  deleteMeasurementView: mocks.deleteMeasurementView,
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
    holes: [
      { center: [40, 30], radius_px: 20, diameter_px: 40, confidence: 0.94, source: 'hough_circle_alt' },
      { center: [140, 30], radius_px: 20, diameter_px: 40, confidence: 0.94, source: 'hough_circle_alt' },
    ],
  }
}

async function stage(wrapper, files = [file()]) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: files, configurable: true })
  await input.trigger('change')
}

async function calibrate(wrapper) {
  wrapper.vm.previewWidth = 160
  wrapper.vm.previewHeight = 120
  const overlay = wrapper.find('.calibration-overlay')
  overlay.element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 160, height: 120 })
  await wrapper.find('.calibration-draw-button').trigger('click')
  await overlay.trigger('mousedown', { button: 0, clientX: 20, clientY: 60 })
  await overlay.trigger('mousemove', { clientX: 140, clientY: 60 })
  await overlay.trigger('mouseup', { clientX: 140, clientY: 60 })
  await wrapper.find('.calibration-draw-button-y').trigger('click')
  await overlay.trigger('mousedown', { button: 0, clientX: 80, clientY: 20 })
  await overlay.trigger('mousemove', { clientX: 80, clientY: 100 })
  await overlay.trigger('mouseup', { clientX: 80, clientY: 100 })
}

describe('MeasurementStudio', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listMeasurementRuns.mockResolvedValue([])
    mocks.captureMeasurement.mockResolvedValue({
      source_key: 'tmp-live-capture',
      source_type: 'live_camera',
      source_filename: 'cam-1.jpg',
      source_camera_id: 'cam-1',
      frame_url: '/api/measurements/files/tmp-live-capture/frame.jpg',
      width: 160,
      height: 120,
    })
    mocks.detectMeasurementJig.mockResolvedValue({
      x: { point_a: [20, 30], point_b: [140, 30] },
      y: { point_a: [20, 30], point_b: [20, 90] },
      confidence: 0.98,
    })
    mocks.processMeasurement.mockResolvedValue(processed())
    mocks.saveMeasurementRun.mockResolvedValue({ id: 'measurement-1', name: 'BRKT-001' })
    mocks.listMeasurementProfiles.mockResolvedValue([])
    mocks.createMeasurementSession.mockResolvedValue({ id: 'session-1', name: 'BRKT-001', status: 'in_progress', views: [] })
    mocks.listMeasurementSessions.mockResolvedValue([])
    mocks.saveMeasurementView.mockResolvedValue({ id: 'view-1', view_status: 'saved', status: 'saved' })
    mocks.updateMeasurementSession.mockResolvedValue({ id: 'session-1', name: 'BRKT-001', status: 'complete', views: [] })
  })

  it('stages an upload without processing it', async () => {
    const wrapper = mount(MeasurementStudio)

    await stage(wrapper)

    expect(wrapper.text()).toContain('bracket.png')
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
  })

  it('stages multiple images as selectable measurement views', async () => {
    const wrapper = mount(MeasurementStudio)

    await stage(wrapper, [file('top.png'), file('reverse.png')])

    expect(wrapper.find('input[type="file"]').attributes('multiple')).toBeDefined()
    expect(wrapper.findAll('.measurement-view-card')).toHaveLength(2)
    expect(wrapper.find('.measurement-view-card.active').text()).toContain('reverse.png')
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
  })

  it('blocks processing until both calibration axes are valid', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)

    expect(wrapper.find('.process-measurement').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('measurement.calibration_reference_incomplete')
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
  })

  it('processes only selected second view', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper, [file('top.png'), file('reverse.png')])
    await wrapper.findAll('.measurement-view-card')[0].trigger('click')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      file: expect.objectContaining({ name: 'top.png' }),
    }))
  })

  it('marks component calibration as review-only by default', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      calibration: expect.objectContaining({ source: 'component_demo' }),
    }))
  })

  it('sends preview coordinate dimensions with manual calibration', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      calibration: expect.objectContaining({ coordinate_width: 160, coordinate_height: 120 }),
    }))
  })

  it('auto-detects jig lines while keeping X and Y length manual', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('.auto-detect-jig').trigger('click')
    await flushPromises()

    expect(mocks.detectMeasurementJig).toHaveBeenCalledWith(expect.objectContaining({ file: expect.any(File) }))
    expect(wrapper.vm.calibrationAxes).toEqual({ x: [[20, 30], [140, 30]], y: [[20, 30], [20, 90]] })
    expect(wrapper.vm.knownMm).toBe(50)
    expect(wrapper.vm.knownMmY).toBe(50)
  })

  it('cancels active calibration drawing when the same axis button is clicked again', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    const button = wrapper.find('.calibration-draw-button')
    await button.trigger('click')
    await button.trigger('click')

    expect(wrapper.find('.calibration-overlay').classes()).not.toContain('active')
  })

  it('clears staged media and measurement values with reset workspace', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    wrapper.vm.runName = 'BRKT-001'
    window.confirm = vi.fn(() => true)
    await wrapper.find('.reset-measurement-workspace').trigger('click')

    expect(wrapper.findAll('.measurement-view-card')).toHaveLength(0)
    expect(wrapper.find('.measurement-preview').exists()).toBe(false)
    expect(wrapper.vm.runName).toBe('')
  })

  it('blocks thickness on TOP_FACE with plain pose guidance', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('thickness_profile')
    await wrapper.find('#pose-type').setValue('TOP_FACE')

    expect(wrapper.find('.pose-warning').exists()).toBe(true)
    expect(wrapper.find('.process-measurement').attributes('disabled')).toBeDefined()
  })

  it('requires a component name before starting a session', async () => {
    const wrapper = mount(MeasurementStudio)
    await wrapper.find('#start-session').trigger('click')

    expect(mocks.createMeasurementSession).not.toHaveBeenCalled()
    expect(wrapper.find('.session-name-error').exists()).toBe(true)
  })

  it('saves selected evaluated view and marks its card saved', async () => {
    const wrapper = mount(MeasurementStudio)
    await wrapper.find('#session-name').setValue('BRKT-001')
    await wrapper.find('#start-session').trigger('click')
    await flushPromises()
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-candidate').trigger('click')
    await wrapper.find('.item-nominal').setValue('60')
    await wrapper.find('.item-tolerance').setValue('2')
    await wrapper.find('.evaluate-measurement').trigger('click')
    await wrapper.find('.save-view').trigger('click')
    await flushPromises()

    expect(mocks.saveMeasurementView).toHaveBeenCalledWith('session-1', expect.objectContaining({
      name: 'BRKT-001',
      source_key: 'tmp-measurement-1',
      items: expect.arrayContaining([expect.objectContaining({ status: 'PASS' })]),
    }))
    expect(wrapper.find('.measurement-view-card').text()).toContain('saved')
  })

  it('blocks completion while a staged view remains unsaved', async () => {
    const wrapper = mount(MeasurementStudio)
    await wrapper.find('#session-name').setValue('BRKT-001')
    await wrapper.find('#start-session').trigger('click')
    await flushPromises()
    await stage(wrapper)

    expect(wrapper.find('.complete-session').attributes('disabled')).toBeDefined()
    expect(mocks.updateMeasurementSession).not.toHaveBeenCalled()
  })

  it('reopens a saved session with all view cards', async () => {
    mocks.listMeasurementSessions.mockResolvedValueOnce([{
      id: 'session-2',
      name: 'BRKT-002',
      status: 'complete',
      created_at: '2026-08-10',
      summary: { status: 'PASS', view_count: 2 },
      views: [],
    }])
    mocks.getMeasurementSession.mockResolvedValueOnce({
      id: 'session-2',
      name: 'BRKT-002',
      status: 'complete',
      summary: { status: 'PASS', view_count: 2 },
      views: [
        { id: 'view-1', source_type: 'image', source_filename: 'top.png', source_url: '/saved/top.png', width: 160, height: 120, pose_type: 'TOP_FACE', view_status: 'saved', processing: { task_type: 'linear_dimension', view_type: 'top' }, calibration: processed().calibration, items: [] },
        { id: 'view-2', source_type: 'image', source_filename: 'reverse.png', source_url: '/saved/reverse.png', width: 160, height: 120, pose_type: 'REVERSE_FACE', view_status: 'saved', processing: { task_type: 'linear_dimension', view_type: 'top' }, calibration: processed().calibration, items: [] },
      ],
    })
    const wrapper = mount(MeasurementStudio)
    await flushPromises()

    expect(wrapper.findAll('.history-session')).toHaveLength(1)
    await wrapper.find('.history-session .history-run').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.measurement-view-card')).toHaveLength(2)
    expect(wrapper.find('.measurement-image').attributes('src')).toBe('/saved/top.png')
    expect(wrapper.find('#pose-type').element.value).toBe('TOP_FACE')
  })

  it('shows staged image calibration guidance before processing', async () => {
    const wrapper = mount(MeasurementStudio)

    await stage(wrapper)

    expect(wrapper.find('.measurement-preview').exists()).toBe(true)
    expect(wrapper.find('.calibration-draw-button').exists()).toBe(true)
    expect(wrapper.find('#task-type').exists()).toBe(true)
    expect(wrapper.find('#view-type').exists()).toBe(true)
  })

  it('shows dual-axis calibration and prefers merged logical edges', async () => {
    mocks.processMeasurement.mockResolvedValue({
      ...processed(),
      calibration: {
        mode: 'manual_axes',
        valid: true,
        x: { point_a: [20, 30], point_b: [140, 30], known_mm: 60 },
        y: { point_a: [20, 30], point_b: [20, 90], known_mm: 30 },
        scale_x_mm_per_px: 0.5,
        scale_y_mm_per_px: 0.5,
      },
      logical_edges: [{
        id: 'LE1',
        points: [[20, 30], [140, 30]],
        length_px: 120,
        confidence: 0.98,
      }],
      candidates: [
        ...processed().candidates,
        { points: [[20, 30], [20, 90]], length_px: 60, confidence: 0.9, source: 'lsd' },
      ],
    })
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)

    expect(wrapper.find('.calibration-draw-button-y').exists()).toBe(true)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.measurement-logical-edge')).toHaveLength(1)
    expect(wrapper.findAll('.measurement-candidate')).toHaveLength(1)
    expect(wrapper.findAll('.calibration-reference line').map((line) => [
      line.attributes('x1'), line.attributes('y1'), line.attributes('x2'), line.attributes('y2'),
    ])).toEqual([
      ['20', '30', '140', '30'],
      ['20', '30', '20', '90'],
    ])
    expect(wrapper.text()).toContain('LE1')
  })

  it('renders processed calibration coordinates directly without display rescaling', async () => {
    mocks.processMeasurement.mockResolvedValue({
      ...processed(),
      width: 320,
      height: 240,
      calibration: {
        mode: 'manual_axes',
        valid: true,
        x: { point_a: [20, 30], point_b: [140, 30], known_mm: 60 },
        y: { point_a: [20, 30], point_b: [20, 90], known_mm: 30 },
        scale_x_mm_per_px: 0.5,
        scale_y_mm_per_px: 0.5,
      },
      logical_edges: [{ id: 'LE1', points: [[20, 30], [140, 30]], length_px: 120, confidence: 0.98 }],
    })
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.calibration-reference line').map((line) => [
      line.attributes('x1'), line.attributes('y1'), line.attributes('x2'), line.attributes('y2'),
    ])).toEqual([
      ['20', '30', '140', '30'],
      ['20', '30', '20', '90'],
    ])
  })

  it('lets an inspector select dimension and corner checks in one process', async () => {
    mocks.processMeasurement.mockResolvedValue({
      ...processed(),
      task_types: ['linear_dimension', 'corner_radius'],
      logical_edges: [{
        id: 'LE1',
        points: [[20, 30], [140, 30]],
        length_px: 120,
        confidence: 0.98,
      }],
      corner_arcs: [{
        id: 'C1',
        center: [20, 30],
        radius_px: 12,
        radius_mm: 6,
        points: [[20, 18], [32, 30]],
        confidence: 0.92,
        geometry: { kind: 'corner_arc', center: [20, 30], radius_mm: 6, points: [[20, 18], [32, 30]] },
      }],
    })
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-corner').setValue(true)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      taskTypes: ['linear_dimension', 'corner_radius'],
    }))
    await wrapper.find('.measurement-corner-candidate').trigger('click')

    expect(wrapper.vm.items[0].type).toBe('corner_radius')
    expect(wrapper.vm.items[0].tolerance).toBe(2)
  })

  it('selects a backend bend candidate with the 0.5 degree default tolerance', async () => {
    mocks.processMeasurement.mockResolvedValue({
      ...processed(),
      task_types: ['bend_angle'],
      bend_candidates: [{
        id: 'B1',
        angle_deg: 135,
        confidence: 0.9,
        geometry: {
          kind: 'bend_angle',
          vertex: [80, 40],
          ray_a: [30, 100],
          ray_b: [140, 100],
          angle_deg: 135,
        },
      }],
    })
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('bend_angle')
    await wrapper.find('#view-type').setValue('profile')
    await wrapper.find('#pose-type').setValue('PROFILE_FACE')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-bend-candidate').trigger('click')

    expect(wrapper.vm.items[0].type).toBe('bend_angle')
    expect(wrapper.vm.items[0].measured).toBe(135)
    expect(wrapper.vm.items[0].tolerance).toBe(0.5)
  })

  it('sends the selected proper task and view to process', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('hole_diameter')
    await wrapper.find('#view-type').setValue('top')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      taskType: 'hole_diameter',
      viewType: 'top',
    }))
  })

  it('adds a hole diameter item with center geometry', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('hole_diameter')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-hole-candidate').trigger('click')

    expect(wrapper.find('.measurement-item').text()).toContain('20.00')
    expect(wrapper.find('.selected-measurement circle').exists()).toBe(true)
  })

  it('adds a hole center-distance item after selecting two holes', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('hole_center_distance')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.findAll('.measurement-hole-candidate')[0].trigger('click')
    expect(wrapper.findAll('.measurement-item')).toHaveLength(0)
    await wrapper.findAll('.measurement-hole-candidate')[1].trigger('click')

    expect(wrapper.find('.measurement-item').text()).toContain('50.00')
  })

  it('adds a hole center-to-edge item after selecting a hole and edge', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('hole_center_to_edge')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.findAll('.measurement-hole-candidate')[0].trigger('click')
    await wrapper.find('.measurement-candidate').trigger('click')

    expect(wrapper.find('.measurement-item').text()).toContain('Hole H1')
  })

  it('keeps the Studio shell fixed and scopes scrolling to History and items', () => {
    const wrapper = mount(MeasurementStudio)

    expect(wrapper.find('.measurement-page').classes()).toContain('measurement-shell')
    expect(wrapper.find('.history-section').classes()).toContain('scroll-region')
    expect(wrapper.find('.items-section').classes()).toContain('scroll-region')
    expect(wrapper.find('.measurement-canvas-panel').classes()).not.toContain('scroll-region')
  })

  it('keeps the left input rail scrollable when Input content grows', () => {
    const wrapper = mount(MeasurementStudio)

    expect(wrapper.find('.measurement-rail-body').classes()).toContain('scroll-region')
    expect(wrapper.find('.measurement-rail-body').find('.source-tabs').exists()).toBe(true)
    expect(wrapper.find('.history-section').classes()).toContain('scroll-region')
  })

  it('processes an uploaded image and renders candidate edges', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({ file: expect.any(File) }))
    expect(wrapper.findAll('.measurement-candidate')).toHaveLength(1)
  })

  it('uses the selected inclination task when an edge is selected', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('inclination')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.find('.measurement-candidate').trigger('click')

    expect(wrapper.vm.items[0].type).toBe('inclination')
    expect(wrapper.vm.items[0].unit).toBe('deg')
  })

  it('builds a bend angle from two selected profile edges', async () => {
    const wrapper = mount(MeasurementStudio)
    mocks.processMeasurement.mockResolvedValueOnce({
      ...processed(),
      task_type: 'bend_angle',
      view_type: 'profile',
      candidates: [
        { points: [[20, 90], [80, 30]], length_px: 84.85, angle: -45, confidence: 0.95, source: 'lsd' },
        { points: [[80, 30], [140, 90]], length_px: 84.85, angle: 45, confidence: 0.95, source: 'lsd' },
      ],
    })
    await stage(wrapper)
    await wrapper.find('#task-type').setValue('bend_angle')
    await wrapper.find('#view-type').setValue('profile')
    await wrapper.find('#pose-type').setValue('PROFILE_FACE')
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    await wrapper.findAll('.measurement-candidate')[0].trigger('click')
    await wrapper.findAll('.measurement-candidate')[1].trigger('click')

    expect(wrapper.vm.items[0].type).toBe('bend_angle')
    expect(wrapper.vm.items[0].unit).toBe('deg')
  })

  it('keeps the image and overlay in one zoomable frame', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    const frame = wrapper.find('.measurement-image-frame')
    expect(frame.find('.measurement-image').exists()).toBe(true)
    expect(frame.find('.measurement-overlay').exists()).toBe(true)
    expect(frame.find('.measurement-line-halo').exists()).toBe(true)
    expect(wrapper.find('.measurement-zoom-controls').exists()).toBe(true)
    expect(wrapper.find('.measurement-zoom-value').text()).toBe('100%')

    await wrapper.find('.measurement-zoom-in').trigger('click')

    expect(wrapper.find('.measurement-zoom-value').text()).toBe('120%')
  })

  it('stages one Live Camera capture before processing', async () => {
    const wrapper = mount(MeasurementStudio)

    await wrapper.find('.source-live').trigger('click')
    await wrapper.find('.camera-select').setValue('cam-1')
    await wrapper.find('.trigger-capture').trigger('click')
    await flushPromises()

    expect(mocks.captureMeasurement).toHaveBeenCalledWith({ cameraId: 'cam-1' })
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
    expect(wrapper.find('.measurement-preview').exists()).toBe(true)
    expect(wrapper.text()).toContain('cam-1.jpg')

    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()

    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      sourceKey: 'tmp-live-capture',
      sourceType: 'live_camera',
      sourceCameraId: 'cam-1',
    }))
  })

  it('appends Live Camera capture to existing staged image', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper, [file('top.png')])
    await wrapper.find('.source-live').trigger('click')
    await wrapper.find('.camera-select').setValue('cam-1')
    await wrapper.find('.trigger-capture').trigger('click')
    await flushPromises()

    expect(wrapper.findAll('.measurement-view-card')).toHaveLength(2)
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
  })

  it('offers Mobile Camera as a client-side capture source', async () => {
    const wrapper = mount(MeasurementStudio)

    await wrapper.find('.source-mobile').trigger('click')

    expect(wrapper.find('.mobile-camera-panel').exists()).toBe(true)
    expect(wrapper.find('.open-mobile-camera').exists()).toBe(true)
    expect(wrapper.find('.capture-mobile').exists()).toBe(true)
    expect(wrapper.find('.mobile-camera-guide').exists()).toBe(true)
  })

  it('stages a Mobile Camera capture before processing', async () => {
    Object.defineProperty(navigator, 'mediaDevices', {
      configurable: true,
      value: {
        getUserMedia: vi.fn().mockResolvedValue({
          getTracks: () => [{ stop: vi.fn() }],
          getVideoTracks: () => [{ getSettings: () => ({ width: 640, height: 480 }) }],
        }),
      },
    })
    const play = vi.spyOn(HTMLMediaElement.prototype, 'play').mockResolvedValue()
    const context = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage: vi.fn() })
    const toBlob = vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback) => callback(new Blob(['frame'], { type: 'image/jpeg' })))
    const wrapper = mount(MeasurementStudio)

    await wrapper.find('.source-mobile').trigger('click')
    await wrapper.find('.open-mobile-camera').trigger('click')
    const video = wrapper.find('video')
    Object.defineProperties(video.element, {
      videoWidth: { value: 640 },
      videoHeight: { value: 480 },
    })
    expect(wrapper.vm.mobileCameraOpen).toBe(true)
    expect(wrapper.vm.processing).toBe(false)
    expect(video.element.videoWidth).toBe(640)
    await wrapper.vm.captureMobile()
    await flushPromises()

    expect(toBlob).toHaveBeenCalled()
    expect(wrapper.vm.localFileName).toBe('mobile.jpg')
    expect(mocks.processMeasurement).not.toHaveBeenCalled()
    expect(wrapper.find('.measurement-preview').exists()).toBe(true)
    expect(wrapper.find('.process-measurement').attributes('disabled')).toBeDefined()

    await calibrate(wrapper)
    await wrapper.find('.process-measurement').trigger('click')
    await flushPromises()
    expect(mocks.processMeasurement).toHaveBeenCalledWith(expect.objectContaining({
      sourceType: 'mobile_camera',
      file: expect.any(File),
    }))

    play.mockRestore()
    context.mockRestore()
    toBlob.mockRestore()
  })

  it('evaluates a selected edge with editable per-item tolerance', async () => {
    const wrapper = mount(MeasurementStudio)
    await stage(wrapper)
    await calibrate(wrapper)
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
    await calibrate(wrapper)
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
      processing: { task_type: 'hole_diameter', view_type: 'top' },
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
    expect(wrapper.find('#task-type').element.value).toBe('hole_diameter')
    expect(wrapper.find('#view-type').element.value).toBe('top')
  })
})
