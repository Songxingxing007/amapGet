import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import App from '../App.vue'

const Blank = { template: '<div />' }
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: '/', component: Blank },
    { path: '/config', component: Blank },
    { path: '/upload', component: Blank },
    { path: '/result/:taskId(\\d+)?', component: Blank },
  ],
})

describe('App shell', () => {
  beforeEach(() => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => ({ json: async () => ({ status: 'ok' }) })),
    )
  })

  it('shows the backend status returned by /api/health', async () => {
    const wrapper = mount(App, { global: { plugins: [ElementPlus, router] } })
    await router.isReady()
    await flushPromises()
    expect(wrapper.text()).toContain('ok')
  })
})
