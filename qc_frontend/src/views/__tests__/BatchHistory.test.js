// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import BatchHistory from '../BatchHistory.vue'

const mocks = vi.hoisted(() => ({
  push: vi.fn(),
  refresh: vi.fn(),
  remove: vi.fn(),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mocks.push }),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

vi.mock('../../composables/useBatchHistory.js', async () => {
  const { ref } = await import('vue')
  return {
    useBatchHistory: () => ({
      batches: ref([
        {
          id: 'batch-1',
          name: 'Shift A',
          cameraName: 'Camera 1',
          createdAt: '2026-06-30T10:00:00',
          imageCount: 2,
          defectCount: 1,
          reviewedCount: 0,
          status: 'done',
        },
      ]),
      refresh: mocks.refresh,
      remove: mocks.remove,
    }),
  }
})

describe('BatchHistory delete flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.remove.mockResolvedValue()
  })

  it('confirms before deleting a batch', async () => {
    const wrapper = mount(BatchHistory)
    const deleteButton = wrapper.findAll('button').find((button) => button.text() === 'common.delete')

    expect(deleteButton).toBeTruthy()
    await deleteButton.trigger('click')

    expect(wrapper.text()).toContain('batches.deleteTitle')

    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    await flushPromises()

    expect(mocks.remove).toHaveBeenCalledWith('batch-1')
    expect(wrapper.find('.dialog').exists()).toBe(false)
  })
})
