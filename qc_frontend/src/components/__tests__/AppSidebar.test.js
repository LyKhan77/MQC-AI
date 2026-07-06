// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { h, reactive } from 'vue'
import AppSidebar from '../AppSidebar.vue'
import sidebarSource from '../AppSidebar.vue?raw'

const route = reactive({ name: 'live' })

vi.mock('vue-router', () => ({
  useRoute: () => route,
}))

vi.mock('../../composables/useI18n.js', () => ({
  useI18n: () => ({ t: (key) => key }),
}))

function mountSidebar(props = { collapsed: false }) {
  return mount(AppSidebar, {
    props,
    attachTo: document.body,
    global: {
      stubs: {
        RouterLink: {
          props: ['to'],
          setup(props, { attrs, slots }) {
            return () =>
              h(
                'a',
                {
                  ...attrs,
                  href: `#${props.to.name}`,
                  class: [
                    attrs.class,
                    props.to.name === route.name ? 'router-link-active' : '',
                  ],
                },
                slots.default?.(),
              )
          },
        },
      },
    },
  })
}

describe('AppSidebar', () => {
  beforeEach(() => {
    route.name = 'live'
    document.body.innerHTML = ''
  })

  it('uses the design-system expanded and collapsed widths', () => {
    expect(sidebarSource).toContain('width: var(--sidebar-left);')
    expect(sidebarSource).toContain('width: 64px;')
  })

  it('highlights the parent group when a child route is active', () => {
    route.name = 'quantity-history'
    const wrapper = mountSidebar()

    const activeGroup = wrapper.find('.nav-group.active')
    expect(activeGroup.exists()).toBe(true)
    expect(activeGroup.text()).toContain('nav.quantity')
  })

  it('shows collapsed rail tooltips for leaf links', () => {
    const wrapper = mountSidebar({ collapsed: true })

    const tooltip = wrapper.find('.tooltip-wrapper .tooltip')
    expect(tooltip.exists()).toBe(true)
    expect(tooltip.text()).toBe('nav.liveMonitor')
  })

  it('toggles a group with Enter from the keyboard', async () => {
    route.name = 'live'
    const wrapper = mountSidebar()
    const quantityGroup = wrapper.findAll('.nav-group')[1]
    const header = quantityGroup.find('.nav-group-header')

    expect(quantityGroup.find('.nav-children').isVisible()).toBe(false)
    await header.trigger('focus')
    await header.trigger('keydown', { key: 'Enter' })

    expect(quantityGroup.find('.nav-children').isVisible()).toBe(true)
  })

  it('moves focus through nav items with arrow keys', async () => {
    const wrapper = mountSidebar()
    const nav = wrapper.find('.sidebar-nav')
    const items = wrapper.findAll('.nav-item')

    await items[0].trigger('focus')
    await nav.trigger('keydown', { key: 'ArrowDown' })

    expect(document.activeElement).toBe(items[1].element)
  })
})
