import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { listRecords, runAoi } from '@/api/client'
import RecordTable from '@/components/RecordTable.vue'

const row = (id: number, name: string) => ({
  id,
  task_id: 1,
  query_name: name,
  match_level: 'exact',
  poi_name: name,
  poi_id: `B${id}`,
  poi_type: '公园',
  typecode: '110101',
  address: '',
  adname: '越秀区',
  lng_gcj02: 113.2,
  lat_gcj02: 23.1,
  lng_wgs84: 113.19,
  lat_wgs84: 23.09,
  aoi_status: 'pending',
  aoi_area_ha: null,
  selected: false,
})

vi.mock('@/api/client', () => ({
  listRecords: vi.fn(async (query: { all_ids_only?: boolean }) =>
    query.all_ids_only
      ? { total: 3, page: 1, page_size: 3, items: [], ids: [1, 2, 3] }
      : { total: 3, page: 1, page_size: 50, items: [row(1, '越秀公园'), row(2, '天河公园')], ids: [1, 2, 3] },
  ),
  runAoi: vi.fn(async () => ({ queued: 2 })),
  exportUrl: (taskId: number, format: string, crs?: string) =>
    `/api/tasks/${taskId}/export?format=${format}${crs ? `&crs=${crs}` : ''}`,
}))

describe('RecordTable', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('loads rows for the task and filters with adname', async () => {
    const wrapper = mount(RecordTable, { props: { taskId: 1 }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as { filters: { adname: string }; reload: (p?: number) => Promise<void> }
    expect(wrapper.text()).toContain('越秀公园')
    vm.filters.adname = '越秀区'
    await vm.reload(1)
    const calls = (listRecords as unknown as { mock: { calls: unknown[][] } }).mock.calls
    const last = calls[calls.length - 1][0] as { adname?: string }
    expect(last.adname).toBe('越秀区')
  })

  it('sends the selected ids when fetching AOI', async () => {
    const wrapper = mount(RecordTable, { props: { taskId: 1 }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as {
      onSelectionChange: (rows: unknown[]) => void
      fetchAoi: () => Promise<void>
      effectiveIds: number[]
    }
    vm.onSelectionChange([row(1, '越秀公园'), row(2, '天河公园')])
    expect(vm.effectiveIds).toEqual([1, 2])
    await vm.fetchAoi()
    expect(runAoi).toHaveBeenCalledWith(1, [1, 2])
  })

  it('uses all filtered ids after select-all', async () => {
    const wrapper = mount(RecordTable, { props: { taskId: 1 }, global: { plugins: [ElementPlus] } })
    await flushPromises()
    const vm = wrapper.vm as unknown as {
      selectAllFiltered: () => Promise<void>
      effectiveIds: number[]
      fetchAoi: () => Promise<void>
    }
    await vm.selectAllFiltered()
    expect(vm.effectiveIds).toEqual([1, 2, 3])
    await vm.fetchAoi()
    expect(runAoi).toHaveBeenCalledWith(1, [1, 2, 3])
  })
})
