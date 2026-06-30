// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'

import Settings from '../Settings.vue'

const mocks = vi.hoisted(() => ({
  refreshClasses: vi.fn(),
  add: vi.fn(),
  update: vi.fn(),
  toggle: vi.fn(),
  remove: vi.fn(),
  refreshCameras: vi.fn(),
  refreshSettings: vi.fn(),
  showToast: vi.fn(),
  log: vi.fn(),
  listModels: vi.fn(),
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({
    t: (key) => key,
    locale: 'en',
    setLocale: vi.fn(),
  }),
}))

vi.mock('../../composables/useCameras.js', async () => {
  const { ref } = await import('vue')
  return {
    useCameras: () => ({
      cameras: ref([]),
      refresh: mocks.refreshCameras,
      addCamera: vi.fn(),
      updateCamera: vi.fn(),
      deleteCamera: vi.fn(),
    }),
  }
})

vi.mock('../../composables/useSettings.js', async () => {
  const { ref } = await import('vue')
  return {
    useSettings: () => ({
      settings: ref({
        confidenceThreshold: 0.5,
        defectStrategy: 'mock',
        activeModel: '',
      }),
      refresh: mocks.refreshSettings,
      update: vi.fn(),
    }),
  }
})

vi.mock('../../composables/useAuditLog.js', () => ({
  useAuditLog: () => ({ log: mocks.log }),
}))

vi.mock('../../composables/useToast.js', () => ({
  useToast: () => ({ showToast: mocks.showToast }),
}))

vi.mock('../../api/models.js', () => ({
  listModels: mocks.listModels,
}))

vi.mock('../../composables/useDefectClasses.js', async () => {
  const { ref } = await import('vue')
  return {
    useDefectClasses: () => ({
      classes: ref([
        { id: 'dc-scratch', name: 'scratch', category: 'coating', color: '#4589ff', enabled: true },
        { id: 'dc-orange-peel', name: 'orange peel', category: 'coating', color: '#ff832b', enabled: false },
        { id: 'dc-porosity', name: 'porosity', category: 'welding', color: '#fa4d56', enabled: true },
      ]),
      refresh: mocks.refreshClasses,
      add: mocks.add,
      update: mocks.update,
      toggle: mocks.toggle,
      remove: mocks.remove,
    }),
  }
})

describe('Settings defect classes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.listModels.mockResolvedValue({ models: [] })
    mocks.add.mockResolvedValue({ id: 'dc-new-flaw' })
    mocks.update.mockResolvedValue({})
    mocks.toggle.mockResolvedValue({})
    mocks.remove.mockResolvedValue()
  })

  it('renders grouped counts and toggles a class', async () => {
    const wrapper = mount(Settings)
    await flushPromises()

    expect(wrapper.text()).toContain('defectClasses.coating')
    expect(wrapper.text()).toContain('1 / 2 defectClasses.on')
    expect(wrapper.text()).toContain('defectClasses.welding')
    expect(wrapper.text()).toContain('1 / 1 defectClasses.on')

    await wrapper.findAll('input[type="checkbox"]')[0].trigger('change')
    expect(mocks.toggle).toHaveBeenCalledWith(expect.objectContaining({ id: 'dc-scratch' }))
  })

  it('adds a defect class from the modal', async () => {
    const wrapper = mount(Settings)
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text().includes('defectClasses.add')).trigger('click')
    await wrapper.find('input[placeholder="defectClasses.namePlaceholder"]').setValue('new flaw')
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    await flushPromises()

    expect(mocks.add).toHaveBeenCalledWith({
      name: 'new flaw',
      category: 'coating',
      color: '#4589ff',
    })
  })

  it('confirms before deleting a defect class', async () => {
    const wrapper = mount(Settings)
    await flushPromises()

    await wrapper.findAll('.dc-icon.danger')[0].trigger('click')
    expect(wrapper.text()).toContain('defectClasses.deleteTitle')

    await wrapper.find('.dialog-actions .btn-primary').trigger('click')
    await flushPromises()

    expect(mocks.remove).toHaveBeenCalledWith('dc-scratch')
  })
})
