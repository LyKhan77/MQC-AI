// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

import Reports from '../Reports.vue'

const mocks = vi.hoisted(() => ({
  addImage: vi.fn(),
  save: vi.fn(),
  text: vi.fn(),
  loadBatch: vi.fn(),
  log: vi.fn(),
  pdf: null,
}))

class FakePdf {
  constructor() {
    mocks.pdf = this
    this.pages = 1
  }

  setFontSize() {}
  setFont() {}
  setTextColor() {}
  setDrawColor() {}
  setFillColor() {}
  line() {}
  rect() {}
  addPage() { this.pages += 1 }
  setPage() {}
  text(...args) { mocks.text(...args) }
  addImage(...args) { mocks.addImage(...args) }
  getNumberOfPages() { return this.pages }
  save(...args) { mocks.save(...args) }
}

vi.mock('jspdf', () => ({ jsPDF: FakePdf }))
vi.mock('../../composables/useI18n.js', () => ({ useI18n: () => ({ t: (key) => key }) }))
vi.mock('../../composables/useBatchHistory.js', async () => {
  const { ref } = await import('vue')
  return {
    useBatchHistory: () => ({
      batches: ref([{ id: 'batch-1', name: 'Batch 1', cameraName: 'Cam 1', modelInfo: { detection: 'model.pt' } }]),
      refresh: vi.fn(),
    }),
  }
})
vi.mock('../../composables/useInspection.js', async () => {
  const { ref } = await import('vue')
  return {
    useInspection: () => ({
      batch: ref({
        id: 'batch-1',
        batch_name: 'Batch 1',
        images: [
          { id: 'image-1', filename: 'pcb-1.png', url: '/pcb-1.png', width: 100, height: 80, status: 'defect', defects: [{ id: 'd-1', type: 'scratch', category: 'coating', confidence: 0.91, polygon: [[10, 10], [30, 10], [30, 25]] }] },
          { id: 'image-2', filename: 'pcb-2.png', url: '/pcb-2.png', width: 100, height: 80, status: 'clean', defects: [] },
        ],
      }),
      loadBatch: mocks.loadBatch,
    }),
  }
})
vi.mock('../../composables/useDefectColor.js', () => ({ useDefectColor: () => ({ colorFor: () => '#f1c21b' }) }))
vi.mock('../../composables/useAuditLog.js', () => ({ useAuditLog: () => ({ log: mocks.log }) }))
vi.mock('../../utils/export.js', () => ({
  defectCropBox: () => ({ x: 10, y: 10, w: 20, h: 15 }),
  fitDimensions: (w, h) => ({ w, h }),
  loadImage: vi.fn(async () => ({ width: 100, height: 80 })),
  renderAnnotated: vi.fn(() => ({ width: 100, height: 80 })),
  renderDefectCrop: vi.fn(() => ({ width: 20, height: 15 })),
}))

describe('Reports', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mocks.pdf = null
  })

  it('offers both report formats', () => {
    const wrapper = mount(Reports)
    expect(wrapper.findAll('input[type="radio"]')).toHaveLength(2)
    expect(wrapper.text()).toContain('reports.defectOnly')
    expect(wrapper.text()).toContain('reports.fullImage')
  })

  it('generates full-image report with annotated image and per-image defect list', async () => {
    const wrapper = mount(Reports)
    await wrapper.find('input[value="full-image"]').setValue()
    await wrapper.find('.btn-primary').trigger('click')
    await flushPromises()

    expect(mocks.addImage).toHaveBeenCalledTimes(2)
    expect(mocks.text.mock.calls.some(([value]) => value === 'reports.defectList')).toBe(true)
    expect(mocks.save).toHaveBeenCalledWith('Batch 1_full-image_report.pdf')
    expect(mocks.log).toHaveBeenCalledWith('REPORT_GENERATED', expect.stringContaining('reports.fullImage'))
  })
})
