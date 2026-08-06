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

function file(name) {
  return new File(['image'], name, { type: 'image/png' })
}

async function stage(wrapper, files) {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', { value: files, configurable: true })
  await input.trigger('change')
  await flushPromises()
}

function processButton(wrapper) {
  return wrapper.find('.process-qc')
}

describe('DirectInspection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('URL', { createObjectURL: vi.fn((value) => `blob:${value.name}`), revokeObjectURL: vi.fn() })
  })

  it('shows qc model and strategy context', () => {
    const wrapper = mount(DirectInspection)
    expect(wrapper.text()).toContain('sam.pt')
    expect(wrapper.text()).toContain('0.55')
    expect(wrapper.text()).toContain('sam3_prompt')
  })

  it('stages uploads without starting detection', async () => {
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('a.png'), file('b.png')])

    expect(mocks.detectInspection).not.toHaveBeenCalled()
    expect(wrapper.findAll('.mask-stage-item')).toHaveLength(2)
  })

  it('processes staged images in order with a mask only for finished masks', async () => {
    let resolveFirst
    const polygon = [[1, 1], [30, 1], [1, 30]]
    mocks.detectInspection
      .mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve }))
      .mockResolvedValueOnce(sample('ins-2'))
    const wrapper = mount(DirectInspection)
    const files = [file('a.png'), file('b.png')]
    await stage(wrapper, files)
    await wrapper.find('.masking-toggle input').setValue(true)
    const preview = wrapper.findAll('.mask-stage-preview').at(0)
    Object.defineProperties(preview.element, {
      naturalWidth: { value: 40 },
      naturalHeight: { value: 40 },
    })
    await preview.trigger('load')
    await wrapper.findComponent({ name: 'MaskEditor' }).vm.$emit('finish', polygon)

    await processButton(wrapper).trigger('click')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalledTimes(1)
    expect(mocks.detectInspection).toHaveBeenCalledWith(expect.objectContaining({
      file: files[0], cropMode: 'full', maskPolygon: polygon,
    }))

    resolveFirst({ ...sample('ins-1'), mask_polygon: polygon, mask_applied: true })
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalledTimes(2)
    expect(mocks.detectInspection).toHaveBeenLastCalledWith(expect.objectContaining({
      file: files[1], cropMode: 'full',
    }))
    expect(mocks.detectInspection.mock.calls[1][0]).not.toHaveProperty('maskPolygon')
    await flushPromises()
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(2)
    await wrapper.findAll('.capture-thumb').at(0).trigger('click')
    expect(wrapper.find('.mask-result-poly').exists()).toBe(true)
  })

  it('requires a changed mask to be finished again before processing it', async () => {
    const polygon = [[1, 1], [30, 1], [1, 30]]
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('masked.png')])
    await wrapper.find('.masking-toggle input').setValue(true)
    const preview = wrapper.find('.mask-stage-preview')
    Object.defineProperties(preview.element, { naturalWidth: { value: 40 }, naturalHeight: { value: 40 } })
    await preview.trigger('load')
    const editor = wrapper.findComponent({ name: 'MaskEditor' })
    await editor.vm.$emit('finish', polygon)
    await editor.vm.$emit('update:modelValue', [[1, 1], [20, 1]])

    await processButton(wrapper).trigger('click')
    await flushPromises()

    expect(mocks.detectInspection).toHaveBeenCalledWith(expect.not.objectContaining({ maskPolygon: expect.anything() }))
    expect(wrapper.text()).toContain('inspection.maskValidation')
  })

  it('resets Auto-crop to Full frame when masking starts', async () => {
    const wrapper = mount(DirectInspection)
    await wrapper.findAll('.seg-btn').at(4).trigger('click')
    await wrapper.find('.masking-toggle input').setValue(true)

    expect(wrapper.findAll('.seg-btn').at(3).classes()).toContain('active')
    expect(wrapper.findAll('.seg-btn').at(4).attributes('disabled')).toBeDefined()
  })

  it('keeps a failed staged image available for retry', async () => {
    mocks.detectInspection
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(sample())
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('retry.png')])
    await processButton(wrapper).trigger('click')
    await flushPromises()
    expect(wrapper.findAll('.mask-stage-item')).toHaveLength(1)
    expect(wrapper.find('.mask-stage-error').text()).toContain('offline')

    await processButton(wrapper).trigger('click')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalledTimes(2)
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(1)
  })

  it('keeps server camera capture on the existing immediate-detect path', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    await wrapper.findAll('.seg-btn').at(1).trigger('click')
    await wrapper.find('select').setValue('cam-1')
    await wrapper.find('.server-cam .btn-sm').trigger('click')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalledWith(expect.objectContaining({ cameraId: 'cam-1' }))
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(1)
  })

  it('keeps mobile camera capture on the existing immediate-detect path', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const context = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue({ drawImage: vi.fn() })
    const toBlob = vi.spyOn(HTMLCanvasElement.prototype, 'toBlob').mockImplementation((callback) => callback(new Blob(['frame'], { type: 'image/jpeg' })))
    const wrapper = mount(DirectInspection)
    await wrapper.findAll('.seg-btn').at(2).trigger('click')
    const video = wrapper.find('video')
    Object.defineProperties(video.element, {
      videoWidth: { value: 20 },
      videoHeight: { value: 10 },
    })
    await wrapper.findAll('.mobile-cam .btn-sm').at(1).trigger('click')
    await flushPromises()

    expect(mocks.detectInspection).toHaveBeenCalledWith(expect.objectContaining({
      cropMode: 'full', file: expect.any(File),
    }))
    context.mockRestore()
    toBlob.mockRestore()
  })

  it('remove drops a capture from the stack', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('a.png')])
    await processButton(wrapper).trigger('click')
    await flushPromises()
    await wrapper.find('.selected-capture .btn-danger-sm').trigger('click')
    expect(wrapper.findAll('.capture-thumb')).toHaveLength(0)
  })

  it('opens a native send review dialog before qc handoff', async () => {
    mocks.detectInspection.mockResolvedValue(sample('ins-9'))
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('a.png')])
    await processButton(wrapper).trigger('click')
    await flushPromises()
    await wrapper.find('.footer-actions .btn-primary').trigger('click')
    expect(wrapper.find('dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('inspection.sendReviewTitle')
    expect(mocks.inspectionToQc).not.toHaveBeenCalled()
  })

  it('disables staged removal and Send to QC while sequential processing is active', async () => {
    let resolveSecond
    mocks.detectInspection
      .mockResolvedValueOnce(sample('ins-1'))
      .mockImplementationOnce(() => new Promise((resolve) => { resolveSecond = resolve }))
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('first.png'), file('second.png')])
    await processButton(wrapper).trigger('click')
    await flushPromises()

    expect(mocks.detectInspection).toHaveBeenCalledTimes(2)
    expect(wrapper.findAll('.mask-stage-heading .btn-danger-sm').every((button) => button.attributes('disabled') !== undefined)).toBe(true)
    expect(wrapper.find('.footer-actions .btn-primary').attributes('disabled')).toBeDefined()
    resolveSecond(sample('ins-2'))
  })

  it('send to studio preserves a finished mask in the qc handoff', async () => {
    const maskPolygon = [[1, 1], [30, 1], [1, 30]]
    mocks.detectInspection.mockResolvedValue({ ...sample('ins-9'), mask_polygon: maskPolygon, mask_applied: true })
    mocks.inspectionToQc.mockResolvedValue({ batch_id: 'batch-1' })
    const wrapper = mount(DirectInspection)
    await stage(wrapper, [file('a.png')])
    await processButton(wrapper).trigger('click')
    await flushPromises()
    await wrapper.find('.footer-actions .btn-primary').trigger('click')
    await wrapper.find('dialog .btn-primary').trigger('click')
    await flushPromises()
    expect(mocks.inspectionToQc).toHaveBeenCalledWith([{
      key: 'ins-9', defects: [{ polygon: [[1, 1], [2, 2], [2, 1]] }], mask_polygon: maskPolygon,
    }])
    expect(mocks.push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })
})
