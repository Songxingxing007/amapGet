import { describe, expect, it } from 'vitest'

import { exportUrl, recordQueryToParams } from '@/api/client'

describe('api client helpers', () => {
  it('drops empty filter values but keeps task id', () => {
    expect(recordQueryToParams({ task_id: 7, adname: '', keyword: undefined, page: 2 })).toEqual({
      task_id: 7,
      page: 2,
    })
  })

  it('keeps boolean filters', () => {
    expect(recordQueryToParams({ task_id: 1, has_aoi: false })).toEqual({ task_id: 1, has_aoi: false })
  })

  it('builds export urls per format and crs', () => {
    expect(exportUrl(7, 'csv')).toBe('/api/tasks/7/export?format=csv')
    expect(exportUrl(7, 'geojson', 'wgs84')).toBe('/api/tasks/7/export?format=geojson&crs=wgs84')
  })
})
