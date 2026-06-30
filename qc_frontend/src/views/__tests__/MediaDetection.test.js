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
const mockSettings = vi.hoisted(() => ({
  settings: { value: { activeModel: 'm.pt', confidenceThreshold: 0.25 } },
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../../composables/useSettings.js', () => ({
  useSettings: () => mockSettings,
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

function imageFile() {
  return new File(['x'], 'a.jpg', { type: 'image/jpeg' })
}

function videoFile() {
  return new File(['x'], 'a.mp4', { type: 'video/mp4' })
}

describe('MediaDetection', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:x')
    globalThis.URL.revokeObjectURL = vi.fn()
    mockSettings.settings.value = { activeModel: 'm.pt', confidenceThreshold: 0.25 }
    detectImage.mockResolvedValue({ image: 'abc', count: 1, detections: [] })
    processImage.mockResolvedValue({
      key: 'media_1',
      count: 2,
      crop_urls: ['/crop/1.jpg', '/crop/2.jpg'],
    })
    approveDetectCrops.mockResolvedValue({ folder: '/data/crops/media_1/x/approved', count: 1 })
    submitBatch.mockResolvedValue({ batch_id: 'batch-1' })
  })

  it('stages a file without processing it', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.stageFile(imageFile())

    expect(detectImage).not.toHaveBeenCalled()
    expect(processImage).not.toHaveBeenCalled()
    expect(wrapper.vm.selectedFile).toBeTruthy()
  })

  it('rejects an invalid file type', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.mode = 'image'
    wrapper.vm.stageFile(videoFile())

    expect(wrapper.vm.selectedFile).toBeNull()
    expect(wrapper.vm.error).toBe('media.invalidImage')
  })

  it('process image run opens the crop review dialog', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.purpose = 'process'
    wrapper.vm.stageFile(imageFile())
    await wrapper.vm.run()
    await flushPromises()

    expect(processImage).toHaveBeenCalled()
    expect(wrapper.vm.reviewCrops).toHaveLength(2)
    expect(wrapper.vm.showReview).toBe(true)
  })

  it('approves selected crops then submits batch and routes to QC', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.sessionKey = 'media_1'
    await wrapper.vm.onReviewConfirm({ batchName: 'b', selectedFiles: ['obj_000.jpg'] })
    await flushPromises()

    expect(approveDetectCrops).toHaveBeenCalledWith('media_1', ['obj_000.jpg'])
    expect(submitBatch).toHaveBeenCalledWith({
      batchName: 'b',
      sourcePath: '/data/crops/media_1/x/approved',
      cameraId: null,
    })
    expect(push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })

  it('does not run without an active model', async () => {
    mockSettings.settings.value = { activeModel: '', confidenceThreshold: 0.25 }
    const wrapper = mount(MediaDetection)

    wrapper.vm.stageFile(imageFile())
    await wrapper.vm.run()

    expect(detectImage).not.toHaveBeenCalled()
    expect(processImage).not.toHaveBeenCalled()
  })
})
