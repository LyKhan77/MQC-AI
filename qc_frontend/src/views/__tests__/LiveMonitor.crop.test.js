// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

import LiveMonitor from '../LiveMonitor.vue'
import { submitBatch } from '../../api/batches.js'
import {
  startCropSession,
  captureDetection,
  approveCrops,
  finalizeCropSession,
} from '../../api/cameras.js'

const push = vi.fn()

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../../composables/useCameras.js', () => ({
  useCameras: () => ({
    cameras: ref([
      {
        id: 'cam-1',
        name: 'Camera 1',
        type: 'rtsp',
        source: 'rtsp://x',
        location: 'Line A',
        status: 'online',
        resolution: '1920x1080',
        fps: 30,
      },
    ]),
    refresh: vi.fn(),
  }),
}))

vi.mock('../../composables/useSettings.js', () => ({
  useSettings: () => ({
    settings: ref({
      activeModel: 'model.pt',
      detectionModel: 'model.pt',
      confidenceThreshold: 0.5,
    }),
  }),
}))

vi.mock('../../composables/useAuditLog.js', () => ({
  useAuditLog: () => ({ log: vi.fn() }),
}))

vi.mock('../../api/batches.js', () => ({
  submitBatch: vi.fn(),
}))

vi.mock('../../api/cameras.js', () => ({
  startCropSession: vi.fn(),
  captureDetection: vi.fn(),
  approveCrops: vi.fn(),
  finalizeCropSession: vi.fn(),
}))

describe('LiveMonitor Auto/Manual crop flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    startCropSession.mockResolvedValue({ session_ts: '2026-06-29-00-00-00' })
    captureDetection.mockResolvedValue({
      captured: 1,
      total_count: 1,
      crop_urls: ['/api/cameras/cam-1/crops/x/obj_000.jpg'],
    })
    finalizeCropSession.mockResolvedValue({
      count: 2,
      folder: '/data/crops/cam/x',
      crop_urls: [
        '/api/cameras/cam-1/crops/x/obj_000.jpg',
        '/api/cameras/cam-1/crops/x/obj_001.jpg',
      ],
    })
    approveCrops.mockResolvedValue({ folder: '/data/crops/cam/x/approved', count: 1 })
    submitBatch.mockResolvedValue({ batch_id: 'batch-1' })
  })

  it('manual capture appends count after starting camera', async () => {
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    wrapper.vm.mode = 'manual'
    await wrapper.vm.startCamera()
    await wrapper.vm.captureOnce()
    await flushPromises()

    expect(startCropSession).toHaveBeenCalledWith('cam-1')
    expect(captureDetection).toHaveBeenCalledWith('cam-1')
    expect(wrapper.vm.objectCount).toBe(1)
  })

  it('review renders finalized crops selected by default with confirm enabled', async () => {
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    await wrapper.vm.openReview()
    await flushPromises()

    expect(wrapper.findAll('.crop-cell')).toHaveLength(2)
    expect(wrapper.vm.selectedCropCount).toBe(2)
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeUndefined()
  })

  it('disables confirm when all crops are deselected', async () => {
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    await wrapper.vm.openReview()
    await flushPromises()
    wrapper.vm.crops.forEach((c) => (c.selected = false))
    await wrapper.vm.$nextTick()

    expect(wrapper.vm.selectedCropCount).toBe(0)
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeDefined()
  })

  it('approves selected crops before submitting batch', async () => {
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    await wrapper.vm.openReview()
    await flushPromises()
    wrapper.vm.crops[1].selected = false
    await wrapper.vm.sendToQC()
    await flushPromises()

    expect(approveCrops).toHaveBeenCalledWith('cam-1', ['obj_000.jpg'])
    expect(submitBatch).toHaveBeenCalledWith({
      batchName: wrapper.vm.batchNameInput,
      sourcePath: '/data/crops/cam/x/approved',
      cameraId: 'cam-1',
    })
    expect(push).toHaveBeenCalledWith({ name: 'qc', query: { batch: 'batch-1' } })
  })
})
