import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getTask, runTask } from '@/api/client'
import TaskProgress from '@/components/TaskProgress.vue'

vi.mock('@/api/client', () => ({
  getTask: vi.fn(async () => ({
    id: 5,
    kind: 'poi',
    status: 'pending',
    source_filename: 'sample.xlsx',
    total: 4,
    done: 4,
    failed: 1,
    paused_reason: '',
  })),
  runTask: vi.fn(async () => ({ started: true, pending: 4 })),
  pauseTask: vi.fn(),
  resumeTask: vi.fn(),
}))

describe('TaskProgress', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubGlobal('window', window)
  })

  it('renders counts from the backend', async () => {
    const wrapper = mount(TaskProgress, { props: { taskId: 5 }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const text = wrapper.text()
    expect(text).toContain('4')
    expect(text).toContain('1')
    const vm = wrapper.vm as unknown as { percent: number; task: { status: string } | null }
    expect(vm.task?.status).toBe('pending')
    expect(vm.percent).toBe(100)
    wrapper.unmount()
  })

  it('starts round one through the API', async () => {
    const wrapper = mount(TaskProgress, { props: { taskId: 5 }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as { startRun: () => Promise<void> }
    await vm.startRun()
    expect(runTask).toHaveBeenCalledWith(5)
    expect(getTask).toHaveBeenCalled()
    wrapper.unmount()
  })
})
