// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import MediaDetection from '../MediaDetection.vue'
import {
  detectImage,
  processImages,
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
  processImages: vi.fn(),
  extractVideo: vi.fn(),
  videoExtractStatus: vi.fn(),
  listDetectCrops: vi.fn(),
  approveDetectCrops: vi.fn(),
}))

vi.mock('../../api/batches.js', () => ({
  submitBatch: vi.fn(),
}))

function imageFile(name = 'a.jpg') {
  return new File(['x'], name, { type: 'image/jpeg' })
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
    processImages.mockResolvedValue({
      key: 'media_1',
      count: 2,
      crop_urls: ['/crop/1.jpg', '/crop/2.jpg'],
    })
    approveDetectCrops.mockResolvedValue({ folder: '/data/crops/media_1/x/approved', count: 1 })
    submitBatch.mockResolvedValue({ batch_id: 'batch-1' })
  })

  it('stages multiple image files without processing them', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.stageFiles([imageFile('a.jpg'), imageFile('b.jpg'), imageFile('c.jpg')])

    expect(detectImage).not.toHaveBeenCalled()
    expect(processImages).not.toHaveBeenCalled()
    expect(wrapper.vm.selectedFiles).toHaveLength(3)
  })

  it('rejects an invalid file type', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.mode = 'image'
    wrapper.vm.stageFiles([videoFile()])

    expect(wrapper.vm.selectedFiles).toHaveLength(0)
    expect(wrapper.vm.error).toBe('media.invalidImage')
  })

  it('removes one staged image', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.stageFiles([imageFile('a.jpg'), imageFile('b.jpg'), imageFile('c.jpg')])
    wrapper.vm.removeFile(1)

    expect(wrapper.vm.selectedFiles.map((item) => item.name)).toEqual(['a.jpg', 'c.jpg'])
    expect(URL.revokeObjectURL).toHaveBeenCalled()
  })

  it('video mode keeps one staged file', () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.switchMode('video')
    wrapper.vm.stageFiles([videoFile()])
    wrapper.vm.stageFiles([new File(['x'], 'b.mp4', { type: 'video/mp4' })])

    expect(wrapper.vm.selectedFiles).toHaveLength(1)
    expect(wrapper.vm.selectedFiles[0].name).toBe('b.mp4')
  })

  it('test image run detects every staged image', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.stageFiles([imageFile('a.jpg'), imageFile('b.jpg')])
    await wrapper.vm.run()
    await flushPromises()

    expect(detectImage).toHaveBeenCalledTimes(2)
    expect(wrapper.vm.imageResults).toHaveLength(2)
    expect(wrapper.vm.progress).toEqual({ done: 2, total: 2 })
  })

  it('process image run opens the crop review dialog', async () => {
    const wrapper = mount(MediaDetection)

    wrapper.vm.purpose = 'process'
    wrapper.vm.stageFiles([imageFile('a.jpg'), imageFile('b.jpg')])
    await wrapper.vm.run()
    await flushPromises()

    expect(processImages).toHaveBeenCalledWith([
      expect.objectContaining({ name: 'a.jpg' }),
      expect.objectContaining({ name: 'b.jpg' }),
    ])
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

    wrapper.vm.stageFiles([imageFile()])
    await wrapper.vm.run()

    expect(detectImage).not.toHaveBeenCalled()
    expect(processImages).not.toHaveBeenCalled()
  })
})
