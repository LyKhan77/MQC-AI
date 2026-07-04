// @vitest-environment jsdom
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import BaseModal from '../BaseModal.vue'

describe('BaseModal', () => {
  it('renders a native dialog when shown', async () => {
    HTMLDialogElement.prototype.showModal = vi.fn(function () {
      this.open = true
    })
    HTMLDialogElement.prototype.close = vi.fn(function () {
      this.open = false
    })

    const wrapper = mount(BaseModal, {
      props: { show: true, title: 'Delete item' },
      slots: { default: '<p>Body</p>', actions: '<button>OK</button>' },
    })

    expect(wrapper.find('dialog.dialog').exists()).toBe(true)
    expect(wrapper.text()).toContain('Delete item')
    expect(wrapper.text()).toContain('Body')
    expect(HTMLDialogElement.prototype.showModal).toHaveBeenCalled()
  })

  it('emits close on cancel', async () => {
    const wrapper = mount(BaseModal, {
      props: { show: true, title: 'Modal' },
    })

    await wrapper.find('dialog').trigger('cancel')

    expect(wrapper.emitted('close')).toBeTruthy()
  })
})
