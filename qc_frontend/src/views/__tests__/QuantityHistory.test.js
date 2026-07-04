// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, RouterLinkStub } from '@vue/test-utils'

import QuantityHistory from '../QuantityHistory.vue'

const mocks = vi.hoisted(() => ({
  refresh: vi.fn(),
  remove: vi.fn(),
  downloadBlob: vi.fn(),
  checkToQc: vi.fn(),
  patchQuantityCheck: vi.fn(),
  showToast: vi.fn(),
}))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('../../composables/useToast.js', () => ({ useToast: () => ({ showToast: mocks.showToast }) }))
vi.mock('../../api/quantity.js', () => ({
  checkToQc: mocks.checkToQc,
  patchQuantityCheck: mocks.patchQuantityCheck,
}))
vi.mock('../../composables/useQuantityHistory.js', async () => {
  const { ref } = await import('vue')
  return {
    useQuantityHistory: () => ({
      checks: ref([
        {
          id: 'qty-1',
          created_at: '2026-07-02T10:00:00',
          source_type: 'image',
          model_used: 'm.pt',
          total_count: 5,
          expected_total: 5,
          tolerance: 0,
          verdict: 'pass',
          per_class_counts: { a: 5 },
          inputs: [
            {
              name: 'a.png',
              total: 3,
              per_class: { a: 3 },
              crops: ['/api/quantity/crops/qty-1/0/obj_000.png', '/api/quantity/crops/qty-1/0/obj_001.png'],
            },
            {
              name: 'b.png',
              total: 2,
              per_class: { a: 2 },
              crops: ['/api/quantity/crops/qty-1/1/obj_000.png'],
            },
          ],
        },
      ]),
      refresh: mocks.refresh,
      remove: mocks.remove,
    }),
  }
})
vi.mock('../../utils/export.js', () => ({ downloadBlob: mocks.downloadBlob }))

function mountView() {
  return mount(QuantityHistory, { global: { stubs: { RouterLink: RouterLinkStub } } })
}

describe('QuantityHistory', () => {
  beforeEach(() => vi.clearAllMocks())

  it('lists saved checks', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('qty-1')
  })

  it('export modal downloads selected checks as CSV', async () => {
    const wrapper = mountView()
    await flushPromises()

    const exportBtn = wrapper.findAll('button').find((b) => b.text().includes('quantity.export'))
    await exportBtn.trigger('click')
    await wrapper.find('.export-dialog button.btn-primary').trigger('click')

    expect(mocks.downloadBlob).toHaveBeenCalledTimes(1)
    const [blob, filename] = mocks.downloadBlob.mock.calls[0]
    expect(filename).toContain('.csv')
    expect(blob).toBeInstanceOf(Blob)
  })

  it('opens an inspect dialog with the saved numbers', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('quantity.inspect')).trigger('click')
    expect(wrapper.find('.inspect-dialog').exists()).toBe(true)
    expect(wrapper.find('.inspect-dialog').text()).toContain('m.pt')
    expect(wrapper.find('.inspect-dialog').text()).toContain('5')
  })

  it('inspect shows a combined gallery of all crops', async () => {
    const wrapper = mountView()
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('quantity.inspect')).trigger('click')
    expect(wrapper.findAll('.gallery-crop')).toHaveLength(3)
  })

  it('sends a check to QC', async () => {
    mocks.checkToQc.mockResolvedValue({ batch_id: 'batch-1' })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('quantity.sendToQc')).trigger('click')
    await flushPromises()
    expect(mocks.checkToQc).toHaveBeenCalledWith('qty-1')
    expect(mocks.showToast).toHaveBeenCalledWith('quantity.sentToQc')
    expect(wrapper.text()).toContain('quantity.openInQc')
  })

  it('renames a check on double-click and save', async () => {
    mocks.patchQuantityCheck.mockResolvedValue({})
    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('.editable-cell').trigger('dblclick')
    const input = wrapper.find('.edit-cell-input')
    await input.setValue('Panel A')
    await input.trigger('blur')
    await flushPromises()
    expect(mocks.patchQuantityCheck).toHaveBeenCalledWith('qty-1', { name: 'Panel A' })
  })

  it('confirms then deletes a check', async () => {
    mocks.remove.mockResolvedValue()
    const wrapper = mountView()
    await flushPromises()
    await wrapper.findAll('button').find((b) => b.text().includes('common.delete')).trigger('click')
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    await flushPromises()
    expect(mocks.remove).toHaveBeenCalledWith('qty-1')
  })
})
