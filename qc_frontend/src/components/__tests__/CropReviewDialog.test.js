// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'

import CropReviewDialog from '../CropReviewDialog.vue'

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

describe('CropReviewDialog', () => {
  it('selects crops and emits selected filenames', async () => {
    const wrapper = mount(CropReviewDialog, {
      props: {
        show: true,
        crops: ['/api/detect/crops/k/x/obj_000.jpg', '/api/detect/crops/k/x/obj_001.jpg'],
      },
    })

    expect(wrapper.findAll('.crop-cell')).toHaveLength(2)
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeUndefined()

    await wrapper.findAll('.crop-head-actions button')[1].trigger('click')
    expect(wrapper.find('.dialog-actions .btn-primary').attributes('disabled')).toBeDefined()

    await wrapper.findAll('input[type="checkbox"]')[0].setValue(true)
    await wrapper.find('.dialog-actions .btn-primary').trigger('click')

    expect(wrapper.emitted('confirm')[0][0]).toMatchObject({
      selectedFiles: ['obj_000.jpg'],
    })
  })
})
