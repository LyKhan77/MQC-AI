// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { ref } from 'vue'

import LiveMonitor from '../LiveMonitor.vue'
import { finalizeCropSession } from '../../api/cameras.js'

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: vi.fn() }),
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
  finalizeCropSession: vi.fn(),
}))

describe('LiveMonitor crop gate', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders finalized crop thumbnails and enables confirm', async () => {
    finalizeCropSession.mockResolvedValue({
      count: 2,
      folder: '/data/crops/cam/x',
      crop_urls: ['/a.jpg', '/b.jpg'],
    })
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    await wrapper.vm.openSendDialog()
    await flushPromises()

    expect(wrapper.findAll('.crop-thumb')).toHaveLength(2)
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeUndefined()
  })

  it('disables confirm when finalize returns no crops', async () => {
    finalizeCropSession.mockResolvedValue({
      count: 0,
      folder: null,
      crop_urls: [],
    })
    const wrapper = mount(LiveMonitor)

    wrapper.vm.selectedCameraId = 'cam-1'
    await wrapper.vm.openSendDialog()
    await flushPromises()

    expect(wrapper.text()).toContain('sendToQC.noCrops')
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeDefined()
  })
})
