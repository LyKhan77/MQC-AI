// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import MaskEditor from '../MaskEditor.vue'

function mountEditor(modelValue = []) {
  const wrapper = mount(MaskEditor, {
    props: { src: '/image.png', width: 100, height: 80, modelValue },
  })
  wrapper.get('[data-testid="mask-canvas"]').element.getBoundingClientRect = () => ({
    left: 0,
    top: 0,
    width: 100,
    height: 80,
  })
  return wrapper
}

describe('MaskEditor', () => {
  it('emits integer image coordinates when a vertex is clicked', async () => {
    const wrapper = mountEditor()

    await wrapper.get('[data-testid="mask-canvas"]').trigger('click', { clientX: 10, clientY: 10 })

    expect(wrapper.emitted('update:modelValue')[0][0]).toEqual([[10, 10]])
  })

  it('finishes a three-point polygon', async () => {
    const wrapper = mountEditor()
    const canvas = wrapper.get('[data-testid="mask-canvas"]')

    await canvas.trigger('click', { clientX: 10, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await wrapper.get('[data-testid="mask-finish"]').trigger('click')

    expect(wrapper.emitted('finish')).toHaveLength(1)
    expect(wrapper.emitted('finish')[0][0]).toEqual([[10, 10], [50, 10], [50, 40]])
  })

  it('finishes on double-click without adding a duplicate vertex', async () => {
    const wrapper = mountEditor()
    const canvas = wrapper.get('[data-testid="mask-canvas"]')

    await canvas.trigger('click', { clientX: 10, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await canvas.trigger('dblclick', { clientX: 50, clientY: 40 })

    expect(wrapper.emitted('finish')[0][0]).toEqual([[10, 10], [50, 10], [50, 40]])
  })

  it('removes native double-click click duplicates before finishing', async () => {
    const wrapper = mountEditor()
    const canvas = wrapper.get('[data-testid="mask-canvas"]')

    await canvas.trigger('click', { clientX: 10, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 10 })
    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await canvas.trigger('dblclick', { clientX: 50, clientY: 40 })

    expect(wrapper.emitted('finish')[0][0]).toEqual([[10, 10], [50, 10], [50, 40]])
  })

  it('undoes the latest vertex and clears the polygon', async () => {
    const wrapper = mountEditor([[10, 10], [50, 10]])
    const canvas = wrapper.get('[data-testid="mask-canvas"]')

    await canvas.trigger('click', { clientX: 50, clientY: 40 })
    await wrapper.get('[data-testid="mask-undo"]').trigger('click')
    expect(wrapper.emitted('update:modelValue').at(-1)[0]).toEqual([[10, 10], [50, 10]])

    await wrapper.get('[data-testid="mask-clear"]').trigger('click')
    expect(wrapper.emitted('clear')).toHaveLength(1)
    expect(wrapper.emitted('update:modelValue').at(-1)[0]).toEqual([])
  })

  it('ignores vertex input while disabled', async () => {
    const wrapper = mountEditor()
    await wrapper.setProps({ disabled: true })

    await wrapper.get('[data-testid="mask-canvas"]').trigger('click', { clientX: 10, clientY: 10 })

    expect(wrapper.emitted('update:modelValue')).toBeUndefined()
  })
})
