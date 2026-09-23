import type { components } from './schema'

export type ConfigView = components['schemas']['ConfigView']
export type ConfigPayload = components['schemas']['ConfigPayload']
export type VerifyResult = components['schemas']['VerifyResult']
export type PreviewResult = components['schemas']['PreviewResult']
export type TaskCreated = components['schemas']['TaskCreated']
export type TaskView = components['schemas']['TaskView']
export type RecordRow = components['schemas']['RecordRow']
export type RecordPage = components['schemas']['RecordPage']

export interface RecordQuery {
  task_id: number
  match_level?: string
  adname?: string
  keyword?: string
  has_aoi?: boolean
  selected?: boolean
  page?: number
  page_size?: number
  all_ids_only?: boolean
}
