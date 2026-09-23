import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { putConfig } from '@/api/client'
import ConfigView from '@/views/ConfigView.vue'

vi.mock('@/api/client', () => ({
  getConfig: vi.fn(async () => ({
    keys_masked: [],
    key_count: 0,
    qps: 3,
    daily_limit_per_key: 4500,
    default_region: '440100',
    sleep_every: 20,
    sleep_min_seconds: 3,
    sleep_max_seconds: 8,
  })),
  putConfig: vi.fn(async (payload: { keys: string[] }) => ({
    keys_masked: ['abcd****5678'],
    key_count: payload.keys.length,
    qps: 3,
    daily_limit_per_key: 4500,
    default_region: '440100',
    sleep_every: 20,
    sleep_min_seconds: 3,
    sleep_max_seconds: 8,
  })),
  verifyConfig: vi.fn(),
}))

describe('ConfigView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('saves only non-empty trimmed keys', async () => {
    const wrapper = mount(ConfigView, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as { form: { keys: string[] }; save: () => Promise<void> }
    vm.form.keys = ['  key-one  ', '', 'key-two']
    await vm.save()
    expect(putConfig).toHaveBeenCalledTimes(1)
    const payload = (putConfig as unknown as { mock: { calls: unknown[][] } }).mock.calls[0][0] as { keys: string[] }
    expect(payload.keys).toEqual(['key-one', 'key-two'])
  })

  it('refuses to save when every key is blank', async () => {
    const wrapper = mount(ConfigView, { global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as { form: { keys: string[] }; save: () => Promise<void> }
    vm.form.keys = ['   ']
    await vm.save()
    expect(putConfig).not.toHaveBeenCalled()
  })
})
