// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuantityDetection from '../QuantityDetection.vue'
import { detectQuantityImage, createQuantityCheck } from '../../api/quantity.js'

const mocks = vi.hoisted(() => ({ log: vi.fn() }))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('../../composables/useAuditLog.js', () => ({ useAuditLog: () => ({ log: mocks.log }) }))
vi.mock('../../composables/useSettings.js', async () => {
  const { ref } = await import('vue')
  return { useSettings: () => ({ settings: ref({ quantityModel: 'count.pt' }), refresh: vi.fn() }) }
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
    detectQuantityImage.mockResolvedValue({ total: 3, per_class: { bolt: 2, nut: 1 }, detections: [], width: 100, height: 100 })
    createQuantityCheck.mockResolvedValue({ id: 'qty-1' })
  })

  it('accumulates counts across images and saves a check', async () => {
    const wrapper = mount(QuantityDetection)

    // add two images through the component's addFiles handler
    await wrapper.vm.addFiles([file('a.png'), file('b.png')])
    await flushPromises()

    expect(wrapper.vm.sessionTotal).toBe(6)
    expect(wrapper.vm.sessionPerClass).toEqual({ bolt: 4, nut: 2 })

    await wrapper.vm.saveCheck()
    await flushPromises()

    expect(createQuantityCheck).toHaveBeenCalledTimes(1)
    const payload = createQuantityCheck.mock.calls[0][0]
    expect(payload.total_count).toBe(6)
    expect(payload.per_class_counts).toEqual({ bolt: 4, nut: 2 })
    expect(mocks.log).toHaveBeenCalledWith('QUANTITY_CHECK', expect.any(String))
  })
})
