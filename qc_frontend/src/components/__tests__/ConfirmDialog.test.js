// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ConfirmDialog from '../ConfirmDialog.vue'

beforeEach(() => {
  HTMLDialogElement.prototype.showModal = vi.fn(function () {
    this.open = true
  })
  HTMLDialogElement.prototype.close = vi.fn(function () {
    this.open = false
  })
})

describe('ConfirmDialog', () => {
  it('emits confirm from the primary action', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        title: 'Delete Batch',
        message: 'Delete batch B-1?',
        confirmLabel: 'Delete',
        cancelLabel: 'Cancel',
      },
    })

    await wrapper.find('.dialog-actions .btn-primary').trigger('click')

    expect(wrapper.emitted('confirm')).toBeTruthy()
  })

  it('emits cancel from the secondary action', async () => {
    const wrapper = mount(ConfirmDialog, {
      props: {
        show: true,
        title: 'Delete Batch',
        message: 'Delete batch B-1?',
      },
    })

    await wrapper.find('.dialog-actions .btn-ghost').trigger('click')

    expect(wrapper.emitted('cancel')).toBeTruthy()
  })
})
