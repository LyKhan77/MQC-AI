// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuantityDetection from '../QuantityDetection.vue'
import { detectQuantityImage, createQuantityCheck, detectQuantityCamera } from '../../api/quantity.js'

const mocks = vi.hoisted(() => ({ log: vi.fn() }))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('../../composables/useAuditLog.js', () => ({ useAuditLog: () => ({ log: mocks.log }) }))
vi.mock('../../composables/useToast.js', () => ({ useToast: () => ({ showToast: vi.fn() }) }))
vi.mock('../../composables/useSettings.js', async () => {
  const { ref } = await import('vue')
  return {
    useSettings: () => ({
      settings: ref({
        quantityModel: 'count.pt',
        quantityConfidenceThreshold: 0.5,
        quantityNmsIou: 0.4,
        quantityAgnosticNms: true,
      }),
      refresh: vi.fn(),
    }),
  }
})
vi.mock('../../composables/useCameras.js', async () => {
  const { ref } = await import('vue')
  return { useCameras: () => ({ cameras: ref([{ id: 'cam-1', name: 'C1' }]), refresh: vi.fn() }) }
})
vi.mock('../../api/quantity.js', () => ({
  detectQuantityImage: vi.fn(),
  createQuantityCheck: vi.fn(),
  detectQuantityCamera: vi.fn(),
}))

function file(name = 'a.png') {
  return new File([new Uint8Array([1, 2, 3])], name, { type: 'image/png' })
}

describe('QuantityDetection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    detectQuantityImage.mockResolvedValue({
      total: 3,
      per_class: { bolt: 2, nut: 1 },
      detections: [
        { box: [0, 0, 5, 5], label: 'bolt', confidence: 0.9 },
        { box: [5, 5, 9, 9], label: 'bolt', confidence: 0.8 },
        { box: [1, 6, 4, 9], label: 'nut', confidence: 0.7 },
      ],
      width: 100,
      height: 100,
      crop_key: 'k1',
      crops: [
        { file: 'obj_000.png', label: 'bolt', box: [0, 0, 5, 5], url: '/api/quantity/crops/_tmp/k1/obj_000.png' },
        { file: 'obj_001.png', label: 'bolt', box: [5, 5, 9, 9], url: '/api/quantity/crops/_tmp/k1/obj_001.png' },
        { file: 'obj_002.png', label: 'nut', box: [1, 6, 4, 9], url: '/api/quantity/crops/_tmp/k1/obj_002.png' },
      ],
    })
    createQuantityCheck.mockResolvedValue({ id: 'qty-1' })
  })

  it('counts from crops, deletes an object, and saves the remainder', async () => {
    const wrapper = mount(QuantityDetection)

    await wrapper.vm.addFiles([file('a.png')])
    await flushPromises()

    expect(wrapper.vm.sessionTotal).toBe(3)
    expect(wrapper.findAll('.det-box')).toHaveLength(3)
    expect(wrapper.findAll('.evi-crop')).toHaveLength(3)

    await wrapper.findAll('button[aria-label="quantity.removeObject"]')[0].trigger('click')
    expect(wrapper.vm.sessionTotal).toBe(2)
    expect(wrapper.findAll('.det-box')).toHaveLength(2)

    await wrapper.vm.saveCheck()
    await flushPromises()

    const payload = createQuantityCheck.mock.calls[0][0]
    expect(payload.total_count).toBe(2)
    expect(payload.inputs[0].crops).toHaveLength(2)
    expect(mocks.log).toHaveBeenCalledWith('QUANTITY_CHECK', expect.any(String))
  })

  it('captures a camera snapshot into the session', async () => {
    detectQuantityCamera.mockResolvedValue({
      total: 2,
      per_class: { pcb: 2 },
      detections: [
        { box: [0, 0, 4, 4], label: 'pcb', confidence: 0.9 },
        { box: [5, 5, 9, 9], label: 'pcb', confidence: 0.8 },
      ],
      width: 100,
      height: 100,
      crop_key: 'k9',
      crops: [
        { file: 'obj_000.png', label: 'pcb', box: [0, 0, 4, 4], url: '/api/quantity/crops/_tmp/k9/obj_000.png' },
        { file: 'obj_001.png', label: 'pcb', box: [5, 5, 9, 9], url: '/api/quantity/crops/_tmp/k9/obj_001.png' },
      ],
      frame_url: '/api/quantity/crops/_tmp/k9/frame.jpg',
    })
    const wrapper = mount(QuantityDetection)
    await wrapper.get('button[aria-label="quantity.sourceCamera"]').trigger('click')
    await wrapper.get('select.cam-select').setValue('cam-1')
    await wrapper.get('button[aria-label="quantity.capture"]').trigger('click')
    await flushPromises()

    expect(wrapper.vm.sessionTotal).toBe(2)
    expect(wrapper.vm.selectedResult.url).toBe('/api/quantity/crops/_tmp/k9/frame.jpg')
  })

  it('shows quantity model context before capture', () => {
    const wrapper = mount(QuantityDetection)

    expect(wrapper.text()).toContain('count.pt')
    expect(wrapper.text()).toContain('0.50')
    expect(wrapper.text()).toContain('0.40')
    expect(wrapper.text()).toContain('quantity.agnosticMerge')
  })

  it('shows detected, removed, corrected, and save readiness after correction', async () => {
    const wrapper = mount(QuantityDetection)

    await wrapper.vm.addFiles([file('a.png')])
    await flushPromises()
    await wrapper.findAll('button[aria-label="quantity.removeObject"]')[0].trigger('click')

    expect(wrapper.text()).toContain('quantity.detectedTotal')
    expect(wrapper.text()).toContain('3')
    expect(wrapper.text()).toContain('quantity.removedObjects')
    expect(wrapper.text()).toContain('1')
    expect(wrapper.text()).toContain('quantity.correctedTotal')
    expect(wrapper.text()).toContain('2')
    expect(wrapper.text()).toContain('quantity.readyToSave')
  })
})
