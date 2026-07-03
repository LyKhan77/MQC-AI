// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import DirectInspection from '../DirectInspection.vue'

const mocks = vi.hoisted(() => ({
  detectInspection: vi.fn(),
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
  inspectionToQc: mocks.inspectionToQc,
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

  it('uploading a file pushes a capture card', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    expect(mocks.detectInspection).toHaveBeenCalled()
    expect(wrapper.findAll('.stack-card')).toHaveLength(1)
  })

  it('remove drops a capture from the stack', async () => {
    mocks.detectInspection.mockResolvedValue(sample())
    const wrapper = mount(DirectInspection)
    const input = wrapper.find('input[type="file"]')
    Object.defineProperty(input.element, 'files', { value: [new File(['x'], 'a.png', { type: 'image/png' })] })
    await input.trigger('change')
    await flushPromises()
    await wrapper.find('.btn-danger-sm').trigger('click')
    expect(wrapper.findAll('.stack-card')).toHaveLength(0)
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
    await flushPromises()
    expect(mocks.inspectionToQc).toHaveBeenCalledWith([{ key: 'ins-9', defects: [{ polygon: [[1, 1], [2, 2], [2, 1]] }] }])
    expect(mocks.push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })
})
