// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import QuantityHistory from '../QuantityHistory.vue'

const mocks = vi.hoisted(() => ({ refresh: vi.fn(), remove: vi.fn(), downloadBlob: vi.fn() }))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('../../composables/useQuantityHistory.js', async () => {
  const { ref } = await import('vue')
  return {
    useQuantityHistory: () => ({
      checks: ref([
        { id: 'qty-1', created_at: '2026-07-02T10:00:00', source_type: 'image', model_used: 'm.pt', total_count: 5, expected_total: 5, tolerance: 0, verdict: 'pass', per_class_counts: { a: 5 }, inputs: [{ name: 'a.png', total: 5, per_class: { a: 5 } }] },
      ]),
      refresh: mocks.refresh,
      remove: mocks.remove,
    }),
  }
})
vi.mock('../../utils/export.js', () => ({ downloadBlob: mocks.downloadBlob }))

describe('QuantityHistory', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists saved checks and exports CSV', async () => {
    const wrapper = mount(QuantityHistory)
    await flushPromises()

    expect(wrapper.text()).toContain('qty-1')

    const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('quantity.exportCsv'))
    await exportBtn.trigger('click')

    expect(mocks.downloadBlob).toHaveBeenCalledTimes(1)
    const [blob, filename] = mocks.downloadBlob.mock.calls[0]
    expect(filename).toContain('.csv')
    expect(blob).toBeInstanceOf(Blob)
  })

  it('opens an inspect dialog with the saved numbers', async () => {
    const wrapper = mount(QuantityHistory)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('quantity.inspect')).trigger('click')
    expect(wrapper.find('.dialog').exists()).toBe(true)
    expect(wrapper.find('.dialog').text()).toContain('a.png')
  })

  it('confirms then deletes a check', async () => {
    mocks.remove.mockResolvedValue()
    const wrapper = mount(QuantityHistory)
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('common.delete')).trigger('click')
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    await flushPromises()
    expect(mocks.remove).toHaveBeenCalledWith('qty-1')
  })
})
