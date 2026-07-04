// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import BatchSidebar from '../BatchSidebar.vue'

const mocks = vi.hoisted(() => ({
  removeImage: vi.fn(),
  resetAndReload: vi.fn(),
  log: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: { batch: 'batch-1' } }),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../../composables/useAuditLog.js', () => ({
  useAuditLog: () => ({ log: mocks.log }),
}))

vi.mock('../../composables/useInspection.js', () => ({
  useInspection: () => ({
    batch: ref({ batch_name: 'B1', source_path: 'src' }),
    images: ref([{ id: 'img-1', filename: 'part.png', status: 'defect', defects: [] }]),
    selectedId: ref('img-1'),
    loading: ref(false),
    error: ref(''),
    reviewedCount: ref(0),
    currentBatchId: ref('batch-1'),
    progress: ref({ done: 0, total: 0 }),
    needsRun: ref(false),
    prepareBatch: vi.fn(),
    runAndLoad: vi.fn(),
    removeImage: mocks.removeImage,
    resetAndReload: mocks.resetAndReload,
    selectImage: vi.fn(),
    toggleReviewed: vi.fn(),
    isReviewed: vi.fn(() => false),
  }),
}))

describe('BatchSidebar confirmations', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    HTMLDialogElement.prototype.showModal = vi.fn(function () { this.open = true })
    HTMLDialogElement.prototype.close = vi.fn(function () { this.open = false })
  })

  it('confirms image delete before deleting', async () => {
    const wrapper = mount(BatchSidebar)
    await wrapper.find('.img-del').trigger('click')
    expect(mocks.removeImage).not.toHaveBeenCalled()
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    expect(mocks.removeImage).toHaveBeenCalledWith('img-1')
  })

  it('confirms reset before resetting', async () => {
    const wrapper = mount(BatchSidebar)
    await wrapper.findAll('.batch-rerun-row button')[1].trigger('click')
    expect(mocks.resetAndReload).not.toHaveBeenCalled()
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    expect(mocks.resetAndReload).toHaveBeenCalledWith('batch-1')
  })
})
