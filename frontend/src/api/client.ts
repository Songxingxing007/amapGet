import axios from 'axios'

import type {
  ConfigPayload,
  ConfigView,
  PreviewResult,
  RecordPage,
  RecordQuery,
  TaskCreated,
  TaskView,
  VerifyResult,
} from './types'

export const http = axios.create({ baseURL: '/api', timeout: 60000 })

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const detail = error?.response?.data?.detail
    if (detail) {
      error.message = typeof detail === 'string' ? detail : JSON.stringify(detail)
    }
    return Promise.reject(error)
  },
)

export function recordQueryToParams(query: RecordQuery): Record<string, string | number | boolean> {
  const params: Record<string, string | number | boolean> = { task_id: query.task_id }
  for (const [key, value] of Object.entries(query)) {
    if (key === 'task_id' || value === undefined || value === null || value === '') continue
    params[key] = value as string | number | boolean
  }
  return params
}

export function exportUrl(taskId: number, format: 'csv' | 'geojson', crs?: 'gcj02' | 'wgs84'): string {
  const params = new URLSearchParams({ format })
  if (crs) params.set('crs', crs)
  return `/api/tasks/${taskId}/export?${params.toString()}`
}

export async function getConfig(): Promise<ConfigView> {
  return (await http.get<ConfigView>('/config')).data
}

export async function putConfig(payload: ConfigPayload): Promise<ConfigView> {
  return (await http.put<ConfigView>('/config', payload)).data
}

export async function verifyConfig(): Promise<VerifyResult> {
  return (await http.post<VerifyResult>('/config/verify')).data
}

export async function previewFile(file: File, maxRows = 10): Promise<PreviewResult> {
  const form = new FormData()
  form.append('file', file)
  return (await http.post<PreviewResult>('/tasks/preview', form, { params: { max_rows: maxRows } })).data
}

export async function createTask(file: File, nameColumn: string, adnameColumn?: string): Promise<TaskCreated> {
  const form = new FormData()
  form.append('file', file)
  form.append('name_column', nameColumn)
  if (adnameColumn) form.append('adname_column', adnameColumn)
  return (await http.post<TaskCreated>('/tasks', form)).data
}

export async function listTasks(): Promise<TaskView[]> {
  return (await http.get<TaskView[]>('/tasks')).data
}

export async function getTask(taskId: number): Promise<TaskView> {
  return (await http.get<TaskView>(`/tasks/${taskId}`)).data
}

export async function runTask(taskId: number): Promise<{ started: boolean; pending: number }> {
  return (await http.post<{ started: boolean; pending: number }>(`/tasks/${taskId}/run`)).data
}

export async function pauseTask(taskId: number): Promise<TaskView> {
  return (await http.post<TaskView>(`/tasks/${taskId}/pause`)).data
}

export async function resumeTask(taskId: number): Promise<TaskView> {
  return (await http.post<TaskView>(`/tasks/${taskId}/resume`)).data
}

export async function listRecords(query: RecordQuery): Promise<RecordPage> {
  return (await http.get<RecordPage>('/records', { params: recordQueryToParams(query) })).data
}

export async function runAoi(taskId: number, recordIds: number[]): Promise<{ started: boolean; pending: number }> {
  return (await http.post<{ started: boolean; pending: number }>(`/tasks/${taskId}/aoi`, { record_ids: recordIds })).data
}
