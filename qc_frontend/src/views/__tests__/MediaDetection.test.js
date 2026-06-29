// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import MediaDetection from '../MediaDetection.vue'
import {
  detectImage,
  processImage,
  approveDetectCrops,
} from '../../api/detect.js'
import { submitBatch } from '../../api/batches.js'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../../api/detect.js', () => ({
  detectImage: vi.fn(),
  uploadVideo: vi.fn(),
  videoStreamUrl: vi.fn((id) => `/api/detect/video/${id}/stream`),
  processImage: vi.fn(),
  extractVideo: vi.fn(),
  videoExtractStatus: vi.fn(),
  listDetectCrops: vi.fn(),
  approveDetectCrops: vi.fn(),
}))

vi.mock('../../api/batches.js', () => ({
  submitBatch: vi.fn(),
}))

function fileEvent() {
  return { target: { files: [new File(['x'], 'a.jpg', { type: 'image/jpeg' })] } }
}

describe('MediaDetection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    detectImage.mockResolvedValue({ image: 'abc', count: 1, detections: [] })
    processImage.mockResolvedValue({
      key: 'media_1',
      count: 1,
      crop_urls: ['/api/detect/crops/media_1/x/obj_000.jpg'],
    })
    approveDetectCrops.mockResolvedValue({ folder: '/data/crops/media_1/x/approved', count: 1 })
    submitBatch.mockResolvedValue({ batch_id: 'batch-1' })
  })

  it('process image opens review dialog with returned crops', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.purpose = 'process'
    wrapper.vm.mode = 'image'
    await wrapper.vm.onFile(fileEvent())
    await flushPromises()

    expect(processImage).toHaveBeenCalled()
    expect(wrapper.findAll('.crop-cell')).toHaveLength(1)
  })

  it('approves selected crops then submits batch and routes to QC', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.sessionKey = 'media_1'
    await wrapper.vm.onReviewConfirm({ batchName: 'batch_a', selectedFiles: ['obj_000.jpg'] })
    await flushPromises()

    expect(approveDetectCrops).toHaveBeenCalledWith('media_1', ['obj_000.jpg'])
    expect(submitBatch).toHaveBeenCalledWith({
      batchName: 'batch_a',
      sourcePath: '/data/crops/media_1/x/approved',
      cameraId: null,
    })
    expect(push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })

  it('test image upload renders preview without opening review dialog', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.purpose = 'test'
    wrapper.vm.mode = 'image'
    await wrapper.vm.onFile(fileEvent())
    await flushPromises()

    expect(detectImage).toHaveBeenCalled()
    expect(processImage).not.toHaveBeenCalled()
    expect(wrapper.find('.result-img').exists()).toBe(true)
    expect(wrapper.find('.dialog-overlay').exists()).toBe(false)
  })
})
