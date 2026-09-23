import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { describe, expect, it, vi } from 'vitest'

import { previewFile } from '@/api/client'
import UploadView from '@/views/UploadView.vue'

const push = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }))

vi.mock('@/api/client', () => ({
  previewFile: vi.fn(async () => ({
    columns: ['大类', '行政区', '公园名称'],
    rows: [['生态公园', '从化区', '广东流溪河国家森林自然公园']],
    suggested_name_column: '公园名称',
    suggested_adname_column: '行政区',
    name_confidence: 'header',
    row_count_preview: 1,
  })),
  createTask: vi.fn(async () => ({ task_id: 12, total: 1, skipped: 0 })),
}))

describe('UploadView', () => {
  it('auto-selects the detected columns after a preview', async () => {
    const wrapper = mount(UploadView, { global: { plugins: [ElementPlus] } })
    const vm = wrapper.vm as unknown as {
      onFile: (f: { raw: File }) => Promise<void>
      nameColumn: string
      adnameColumn: string
      create: () => Promise<void>
    }
    await vm.onFile({ raw: new File(['x'], 'sample.xlsx') })
    await flushPromises()
    expect(previewFile).toHaveBeenCalled()
    expect(vm.nameColumn).toBe('公园名称')
    expect(vm.adnameColumn).toBe('行政区')
    await vm.create()
    expect(push).toHaveBeenCalledWith('/result/12')
  })
})
