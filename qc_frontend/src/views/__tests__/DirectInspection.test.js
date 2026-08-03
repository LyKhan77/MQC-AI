// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import DirectInspection from '../DirectInspection.vue'

const mocks = vi.hoisted(() => ({
  detectInspection: vi.fn(),
  previewAutocrop: vi.fn(),
  inspectionToQc: vi.fn(),
  push: vi.fn(),
}))

vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (k) => k }) }))
vi.mock('vue-router', () => ({ useRouter: () => ({ push: mocks.push }) }))
vi.mock('../../composables/useCameras.js', async () => {
  const { ref } = await import('vue')
  return { useCameras: () => ({ cameras: ref([{ id: 'cam-1', name: 'Cam 1' }]), refresh: vi.fn() }) }
})
vi.mock('../../api/inspection.js', () => ({
  detectInspection: mocks.detectInspection,
  previewAutocrop: mocks.previewAutocrop,
  inspectionToQc: mocks.inspectionToQc,
}))
vi.mock('../../composables/useSettings.js', async () => {
  const { ref } = await import('vue')
  return {
    useSettings: () => ({
      settings: ref({
        qcModel: 'sam.pt',
        qcConfidenceThreshold: 0.55,
        defectStrategy: 'sam3_prompt',
      }),
      refresh: vi.fn(),
    }),
  }
})
vi.mock('../../components/BaseModal.vue', () => ({
  // ponytail: stub the shared modal shell so tests assert on the dialog contract, not internals
  default: {
    name: 'BaseModal',
    props: ['show', 'title', 'size'],
    emits: ['close'],
    template: '<dialog v-show="show" class="dialog"><div v-if="show"><h3>{{ title }}</h3><slot/><div class="dialog-actions"><slot name="actions"/></div></div></dialog>',
  },
}))

function sample(key = 'ins-1') {
  return {
    key,
    width: 40,
    height: 40,
    verdict: 'defect',
    defects: [{ polygon: [[1, 1], [2, 2], [2, 1]] }],
    frame_url: `/f/${key}`,
  }
}

describe('DirectInspection', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows qc model and strategy context', () => {
    const wrapper = mount(DirectInspection)
    expect(wrapper.text()).toContain('sam.pt')
    expect(wrapper.text()).toContain('0.55')
    expect(wrapper.text()).toContain('sam3_prompt')
  })

  it('uploading a file pushes a capture card', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalled()
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(1)
  })

  it('selects the newest capture after multiple uploads', async () => {
    mocks.detectInspection
      .mockResolvedValueOnce(sample('ins-1'))
      .mockResolvedValueOnce(sample('ins-2'))
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' }), new File(['y'], 'b.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    expect(wrapper.find('.selected-capture img').attributes('src')).toBe('/f/ins-2')
  })

  it('sends auto-crop debug flag and shows debug frame', async () => {
    mocks.detectInspection.mockResolvedValue({ ...sample(), debug_frame_url: '/debug/ins-1.jpg' })
    const wrapper = mount(DirectInspection)
    await wrapper.findAll('.seg-btn').at(4).trigger('click')
    await wrapper.find('input[type="checkbox"]').setValue(true)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalledWith(expect.objectContaining({ cropMode: 'auto', debugCrop: true }))
    expect(wrapper.find('.auto-crop-debug img').attributes('src')).toBe('/debug/ins-1.jpg')
  })

  it('summarizes captures and defects for review', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    expect(wrapper.text()).toContain('inspection.captures')
    expect(wrapper.text()).toContain('inspection.defects')
    expect(wrapper.text()).toContain('inspection.cleanCaptures')
  })

  it('remove drops a capture from the stack', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    await wrapper.find('.btn-danger-sm').trigger('click')
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(0)
  })

  it('opens a native send review dialog before qc handoff', async () => {
    mocks.detectInspection.mockResolvedValue(sample('ins-9'))
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    await wrapper.find('.footer-actions .btn-primary').trigger('click')
    expect(wrapper.find('dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('inspection.sendReviewTitle')
    expect(mocks.inspectionToQc).not.toHaveBeenCalled()
  })

  it('send to studio calls api with captures and routes to qc', async () => {
    mocks.detectInspection.mockResolvedValue(sample('ins-9'))
    mocks.inspectionToQc.mockResolvedValue({ batch_id: 'batch-1' })
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    await wrapper.find('.footer-actions .btn-primary').trigger('click')
    await wrapper.find('dialog .btn-primary').trigger('click')
    await flushPromises()
    expect(mocks.inspectionToQc).toHaveBeenCalledWith([{ key: 'ins-9', defects: [{ polygon: [[1, 1], [2, 2], [2, 1]] }] }])
    expect(mocks.push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })
})
