// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { nextTick } from 'vue'

import InspectionCanvas from '../InspectionCanvas.vue'
import { segmentDefect } from '../../api/batches.js'

const mocks = vi.hoisted(() => ({
  state: {},
  clearDefectSelection: vi.fn(),
  selectDefect: vi.fn(),
  addDefect: vi.fn(),
  updateDefect: vi.fn(),
  removeDefect: vi.fn(),
  toggleReviewed: vi.fn(),
  toggleEditMode: vi.fn(),
  log: vi.fn(),
}))

vi.mock('../../composables/useInspection.js', async () => {
  const { ref } = await import('vue')
  mocks.state = {
    selected: ref({
      id: 'img-1',
      url: '/image.png',
      filename: 'image.png',
      width: 100,
      height: 100,
      defects: [],
    }),
    selectedDefectId: ref(null),
    hoveredDefectId: ref(null),
    editMode: ref(true),
    currentBatchId: ref('batch-1'),
  }
  return {
    useInspection: () => ({
      ...mocks.state,
      toggleReviewed: mocks.toggleReviewed,
      isReviewed: vi.fn(() => false),
      toggleEditMode: mocks.toggleEditMode,
      selectDefect: mocks.selectDefect,
      clearDefectSelection: mocks.clearDefectSelection,
      addDefect: mocks.addDefect,
      updateDefect: mocks.updateDefect,
      removeDefect: mocks.removeDefect,
    }),
  }
})

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({
    t: (key) => ({
      'qc.editTools': 'Canvas edit tools',
      'qc.toolSelect': 'Select',
      'qc.toolAdd': 'Draw',
      'qc.toolSamPoint': 'SAM point',
      'qc.toolSamBox': 'SAM box',
      'qc.toolDelete': 'Delete',
      'qc.toolReshape': 'Reshape',
      'qc.finishDrawing': 'Finish',
      'qc.pickClass': 'Pick class',
      'qc.toggleAnnotation': 'Toggle Annotation',
      'qc.annotationsOn': 'Annotations',
      'qc.annotationsOff': 'Off',
      'qc.markReviewed': 'Mark Reviewed',
      'qc.markUnreviewed': 'Unmark Review',
      'qc.mode': 'Mode',
      'qc.view': 'View',
      'qc.edit': 'Edit',
      'qc.zoomOut': 'Zoom Out',
      'qc.zoomIn': 'Zoom In',
      'qc.zoomReset': 'Reset Zoom',
      'qc.zoomResetShort': 'Reset',
      'qc.samHintPoint': 'Click a defect to auto-segment.',
      'qc.samHintBox': 'Drag a box around a defect.',
      'qc.drawHint': 'Click to add points, double-click to finish, Esc to cancel.',
      'qc.segmenting': 'Segmenting...',
      'qc.samEmpty': 'No shape found - try again.',
      'qc.reshapeHint': 'Drag a point to reshape.',
      'qc.needThreePoints': 'Draw at least 3 points.',
      'qc.selectImage': 'Select an image from batch...',
      'common.cancel': 'Cancel',
    }[key] ?? key),
  }),
}))

vi.mock('../../composables/useDefectColor.js', () => ({
  useDefectColor: () => ({ colorFor: vi.fn(() => '#4589ff') }),
}))

vi.mock('../../composables/useDefectClasses.js', async () => {
  const { ref } = await import('vue')
  return {
    useDefectClasses: () => ({
      classes: ref([{ id: 'dc-scratch', name: 'scratch', category: 'coating', color: '#4589ff', enabled: true }]),
    }),
  }
})

vi.mock('../../composables/useAuditLog.js', () => ({
  useAuditLog: () => ({ log: mocks.log }),
}))

vi.mock('../../api/batches.js', () => ({
  segmentDefect: vi.fn(),
}))

describe('InspectionCanvas edit dock', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.state.selectedDefectId.value = null
    segmentDefect.mockResolvedValue({ polygon: [[1, 1], [20, 1], [20, 20]] })
  })

  it('renders icon buttons with visible labels', () => {
    const wrapper = mount(InspectionCanvas)

    const dockText = wrapper.find('.tool-dock').text()

    expect(dockText).toContain('Select')
    expect(dockText).toContain('Draw')
    expect(dockText).toContain('SAM point')
    expect(dockText).toContain('SAM box')
    expect(dockText).toContain('Reshape')
    expect(dockText).toContain('Delete')
    expect(wrapper.findAll('.tool-icon')).toHaveLength(6)
  })

  it('shows Cancel for an active SAM tool and Escape returns to Select', async () => {
    const wrapper = mount(InspectionCanvas)

    await wrapper.get('button[aria-label="SAM point"]').trigger('click')

    expect(wrapper.find('.tool-dock').text()).toContain('Cancel')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()

    expect(wrapper.get('button[aria-label="Select"]').attributes('aria-pressed')).toBe('true')
  })

  it('lets the class picker cancel a pending SAM polygon', async () => {
    const wrapper = mount(InspectionCanvas)

    await wrapper.get('button[aria-label="SAM point"]').trigger('click')
    const overlay = wrapper.get('svg.overlay')
    overlay.element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })
    await overlay.trigger('click', { clientX: 10, clientY: 20 })
    await flushPromises()

    expect(wrapper.text()).toContain('Pick class')

    await wrapper.get('.class-picker button[aria-label="Cancel"]').trigger('click')

    expect(wrapper.text()).not.toContain('Pick class')
    expect(wrapper.get('button[aria-label="Select"]').attributes('aria-pressed')).toBe('true')
  })

  it('ignores a SAM response after Cancel', async () => {
    let resolveSegment
    segmentDefect.mockReturnValue(new Promise((resolve) => {
      resolveSegment = resolve
    }))
    const wrapper = mount(InspectionCanvas)

    await wrapper.get('button[aria-label="SAM point"]').trigger('click')
    const overlay = wrapper.get('svg.overlay')
    overlay.element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })
    overlay.element.dispatchEvent(new MouseEvent('click', { bubbles: true, clientX: 10, clientY: 20 }))
    await nextTick()

    await wrapper.get('.tool-dock button[aria-label="Cancel"]').trigger('click')
    resolveSegment({ polygon: [[1, 1], [20, 1], [20, 20]] })
    await flushPromises()

    expect(wrapper.text()).not.toContain('Pick class')
    expect(wrapper.get('button[aria-label="Select"]').attributes('aria-pressed')).toBe('true')
  })
})

describe('InspectionCanvas vertex reshaping', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.state.selected.value.defects = [
      { id: 'd-1', type: 'scratch', category: 'coating', confidence: 1, polygon: [[10, 10], [20, 10], [20, 20]] },
    ]
    mocks.state.selectedDefectId.value = 'd-1'
  })

  async function enterReshape(wrapper) {
    await wrapper.get('button[aria-label="Reshape"]').trigger('click')
    await nextTick()
    const overlay = wrapper.get('svg.overlay')
    overlay.element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })
    return overlay
  }

  it('shows a handle per vertex when Reshape is active on a selected defect', async () => {
    const wrapper = mount(InspectionCanvas)
    await enterReshape(wrapper)
    expect(wrapper.findAll('.reshape-handle')).toHaveLength(3)
  })

  it('commits a moved vertex on drop via updateDefect and logs the action', async () => {
    const wrapper = mount(InspectionCanvas)
    await enterReshape(wrapper)
    const scroll = wrapper.get('.canvas-scroll')

    await wrapper.findAll('.reshape-hit')[0].trigger('mousedown', { clientX: 10, clientY: 10 })
    await scroll.trigger('mousemove', { clientX: 50, clientY: 60 })
    await scroll.trigger('mouseup')
    await flushPromises()

    expect(mocks.updateDefect).toHaveBeenCalledTimes(1)
    const [imageId, defectId, patch] = mocks.updateDefect.mock.calls[0]
    expect(imageId).toBe('img-1')
    expect(defectId).toBe('d-1')
    expect(patch.polygon[0]).toEqual([50, 60])
    expect(patch.polygon[1]).toEqual([20, 10])
    expect(mocks.log).toHaveBeenCalledWith('DEFECT_RESHAPED', expect.stringContaining('d-1'))
  })

  it('does not commit when the press does not exceed the drag threshold', async () => {
    const wrapper = mount(InspectionCanvas)
    await enterReshape(wrapper)
    const scroll = wrapper.get('.canvas-scroll')

    await wrapper.findAll('.reshape-hit')[0].trigger('mousedown', { clientX: 10, clientY: 10 })
    await scroll.trigger('mousemove', { clientX: 11, clientY: 11 })
    await scroll.trigger('mouseup')
    await flushPromises()

    expect(mocks.updateDefect).not.toHaveBeenCalled()
  })

  it('reverts the dragged vertex on Escape without committing', async () => {
    const wrapper = mount(InspectionCanvas)
    await enterReshape(wrapper)
    const scroll = wrapper.get('.canvas-scroll')

    await wrapper.findAll('.reshape-hit')[0].trigger('mousedown', { clientX: 10, clientY: 10 })
    await scroll.trigger('mousemove', { clientX: 50, clientY: 60 })
    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await nextTick()
    await scroll.trigger('mouseup')
    await flushPromises()

    expect(mocks.updateDefect).not.toHaveBeenCalled()
    expect(wrapper.findAll('.reshape-handle')[0].attributes('cx')).toBe('10')
  })

  it('clears the defect selection when clicking empty canvas', async () => {
    const wrapper = mount(InspectionCanvas)
    const overlay = wrapper.get('svg.overlay')
    overlay.element.getBoundingClientRect = () => ({ left: 0, top: 0, width: 100, height: 100 })

    await overlay.trigger('click', { clientX: 80, clientY: 80 })

    expect(mocks.clearDefectSelection).toHaveBeenCalled()
  })
})
