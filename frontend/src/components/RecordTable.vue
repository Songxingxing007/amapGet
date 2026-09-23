<template>
  <div>
    <el-form inline class="filters">
      <el-form-item label="匹配度">
        <el-select v-model="filters.matchLevel" multiple clearable placeholder="全部" style="width: 220px">
          <el-option v-for="level in ['exact', 'contains', 'weak']" :key="level" :label="level" :value="level" />
        </el-select>
      </el-form-item>
      <el-form-item label="行政区">
        <el-input v-model="filters.adname" placeholder="多个用逗号分隔" clearable style="width: 180px" />
      </el-form-item>
      <el-form-item label="关键词">
        <el-input v-model="filters.keyword" clearable style="width: 180px" />
      </el-form-item>
      <el-form-item label="AOI">
        <el-select v-model="filters.hasAoi" clearable placeholder="全部" style="width: 130px">
          <el-option label="已有" :value="true" />
          <el-option label="尚未获取" :value="false" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="reload(1)">查询</el-button>
        <el-button :disabled="page.total === 0" @click="selectAllFiltered">全选筛选结果</el-button>
        <el-button :disabled="effectiveIds.length === 0" @click="fetchAoi">
          对选中项取 AOI（{{ effectiveIds.length }}）
        </el-button>
        <el-dropdown @command="download">
          <el-button :disabled="page.total === 0">导出</el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="csv">CSV</el-dropdown-item>
              <el-dropdown-item command="wgs84">GeoJSON（WGS-84）</el-dropdown-item>
              <el-dropdown-item command="gcj02">GeoJSON（GCJ-02）</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-form-item>
    </el-form>

    <div class="hint">默认只看名称完全一致的候选；清空「匹配度」筛选可看全部候选。</div>
    <el-alert
      v-if="allFilteredIds"
      type="info"
      :closable="false"
      :title="`已选中当前筛选结果的全部 ${allFilteredIds.length} 条`"
    />

    <el-table :data="page.items" row-key="id" border size="small" @selection-change="onSelectionChange">
      <el-table-column type="selection" width="48" />
      <el-table-column prop="query_name" label="查询名称" min-width="170" />
      <el-table-column prop="match_level" label="匹配度" width="100" />
      <el-table-column prop="poi_name" label="POI 名称" min-width="190" />
      <el-table-column prop="adname" label="行政区" width="100" />
      <el-table-column prop="typecode" label="分类码" width="90" />
      <el-table-column prop="poi_id" label="POI ID" width="140" />
      <el-table-column prop="aoi_status" label="AOI" width="100" />
      <el-table-column prop="aoi_area_ha" label="面积(ha)" width="100" />
    </el-table>

    <el-pagination
      class="pager"
      layout="total, sizes, prev, pager, next"
      :total="page.total"
      :current-page="currentPage"
      :page-size="pageSize"
      :page-sizes="[20, 50, 100, 200]"
      @current-change="reload"
      @size-change="onSizeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, reactive, ref, watch } from 'vue'

import { exportUrl, listRecords, runAoi } from '@/api/client'
import type { RecordPage, RecordRow } from '@/api/types'

const props = defineProps<{ taskId: number }>()

const filters = reactive<{ matchLevel: string[]; adname: string; keyword: string; hasAoi: boolean | null }>({
  matchLevel: ['exact'],
  adname: '',
  keyword: '',
  hasAoi: null,
})
const page = ref<RecordPage>({ total: 0, page: 1, page_size: 50, items: [], ids: [] })
const currentPage = ref(1)
const pageSize = ref(50)
const selectedIds = ref<number[]>([])
const allFilteredIds = ref<number[] | null>(null)

const effectiveIds = computed(() => allFilteredIds.value ?? selectedIds.value)

function baseQuery() {
  return {
    task_id: props.taskId,
    match_level: filters.matchLevel.join(',') || undefined,
    adname: filters.adname || undefined,
    keyword: filters.keyword || undefined,
    has_aoi: filters.hasAoi === null ? undefined : filters.hasAoi,
  }
}

async function reload(targetPage = currentPage.value) {
  if (!props.taskId) return
  currentPage.value = targetPage
  allFilteredIds.value = null
  try {
    page.value = await listRecords({ ...baseQuery(), page: currentPage.value, page_size: pageSize.value })
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function onSizeChange(size: number) {
  pageSize.value = size
  void reload(1)
}

function onSelectionChange(rows: RecordRow[]) {
  selectedIds.value = rows.map((row) => row.id)
  allFilteredIds.value = null
}

async function selectAllFiltered() {
  try {
    const result = await listRecords({ ...baseQuery(), all_ids_only: true })
    allFilteredIds.value = result.ids
    ElMessage.success(`已选中 ${result.ids.length} 条`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function fetchAoi() {
  const ids = effectiveIds.value
  if (!ids.length) return
  try {
    const result = await runAoi(props.taskId, ids)
    ElMessage.success(`已加入队列 ${result.pending} 条`)
    await reload(1)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

function download(command: string) {
  const url =
    command === 'csv' ? exportUrl(props.taskId, 'csv') : exportUrl(props.taskId, 'geojson', command as 'gcj02' | 'wgs84')
  window.open(url, '_blank')
}

watch(() => props.taskId, () => void reload(1), { immediate: true })

defineExpose({ filters, page, effectiveIds, selectedIds, allFilteredIds, reload, selectAllFiltered, fetchAoi, onSelectionChange, download })
</script>

<style scoped>
.filters {
  margin-bottom: 8px;
}
.hint {
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}
.pager {
  margin-top: 12px;
}
</style>
