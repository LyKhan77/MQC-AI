// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuantityDetection from '../QuantityDetection.vue'
import { detectQuantityImage, createQuantityCheck } from '../../api/quantity.js'

const mocks = vi.hoisted(() => ({ log: vi.fn() }))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('../../composables/useAuditLog.js', () => ({ useAuditLog: () => ({ log: mocks.log }) }))
vi.mock('../../composables/useToast.js', () => ({ useToast: () => ({ showToast: vi.fn() }) }))
vi.mock('../../composables/useSettings.js', async () => {
  const { ref } = await import('vue')
  return { useSettings: () => ({ settings: ref({ quantityModel: 'count.pt', quantityConfidenceThreshold: 0.5 }), refresh: vi.fn() }) }
})
vi.mock('../../api/quantity.js', () => ({
  detectQuantityImage: vi.fn(),
  createQuantityCheck: vi.fn(),
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
    })
    createQuantityCheck.mockResolvedValue({ id: 'qty-1' })
  })

  it('accumulates counts, draws boxes, and saves a check with per-image inputs', async () => {
    const wrapper = mount(QuantityDetection)

    await wrapper.vm.addFiles([file('a.png'), file('b.png')])
    await flushPromises()

    expect(wrapper.vm.sessionTotal).toBe(6)
    expect(wrapper.vm.sessionPerClass).toEqual({ bolt: 4, nut: 2 })
    expect(wrapper.findAll('.det-box')).toHaveLength(6)

    await wrapper.vm.saveCheck()
    await flushPromises()

    const payload = createQuantityCheck.mock.calls[0][0]
    expect(payload.total_count).toBe(6)
    expect(payload.inputs).toHaveLength(2)
    expect(payload.inputs[0]).toMatchObject({ name: 'a.png', total: 3, per_class: { bolt: 2, nut: 1 } })
    expect(mocks.log).toHaveBeenCalledWith('QUANTITY_CHECK', expect.any(String))
  })
})
