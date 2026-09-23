<template>
  <el-card shadow="never">
    <template #header>上传名单</template>
    <el-upload
      drag
      :auto-upload="false"
      :show-file-list="false"
      :on-change="onFile"
      accept=".csv,.xlsx,.xlsm"
    >
      <div class="drop">把 CSV 或 Excel 拖到这里，或点击选择文件</div>
    </el-upload>

    <div v-if="preview" class="preview">
      <p class="hint">
        识别到 {{ preview.columns.length }} 列，预览 {{ preview.row_count_preview }} 行；名称列建议：
        <strong>{{ preview.suggested_name_column || '未识别，请手动选择' }}</strong>
        （{{ preview.name_confidence === 'header' ? '按表头匹配' : preview.name_confidence === 'heuristic' ? '按内容推断' : '未识别' }}）
      </p>
      <el-form label-width="140px">
        <el-form-item label="名称列">
          <el-select v-model="nameColumn" placeholder="选择名称列" style="width: 260px" data-test="name-column">
            <el-option v-for="column in preview.columns" :key="column" :label="column" :value="column" />
          </el-select>
        </el-form-item>
        <el-form-item label="行政区列（可选）">
          <el-select v-model="adnameColumn" clearable placeholder="不使用" style="width: 260px">
            <el-option v-for="column in preview.columns" :key="column" :label="column" :value="column" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-table :data="preview.rows" size="small" max-height="260" border>
        <el-table-column v-for="(column, index) in preview.columns" :key="column" :label="column">
          <template #default="scope">{{ scope.row[index] }}</template>
        </el-table-column>
      </el-table>
      <el-button
        type="primary"
        class="create"
        :loading="creating"
        :disabled="!nameColumn"
        @click="create"
      >
        创建任务
      </el-button>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { createTask, previewFile } from '@/api/client'
import type { PreviewResult } from '@/api/types'

const router = useRouter()
const preview = ref<PreviewResult | null>(null)
const nameColumn = ref('')
const adnameColumn = ref('')
const creating = ref(false)
const pendingFile = ref<File | null>(null)

async function onFile(uploadFile: { raw?: File }) {
  const file = uploadFile.raw
  if (!file) return
  pendingFile.value = file
  try {
    const result = await previewFile(file)
    preview.value = result
    nameColumn.value = result.suggested_name_column ?? ''
    adnameColumn.value = result.suggested_adname_column ?? ''
    if (!result.suggested_name_column) {
      ElMessage.warning('没能识别出名称列，请手动选择')
    }
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function create() {
  if (!pendingFile.value || !nameColumn.value) return
  creating.value = true
  try {
    const created = await createTask(pendingFile.value, nameColumn.value, adnameColumn.value || undefined)
    ElMessage.success(`已创建任务，共 ${created.total} 条名称`)
    router.push(`/result/${created.task_id}`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    creating.value = false
  }
}

defineExpose({ preview, nameColumn, adnameColumn, onFile, create })
</script>

<style scoped>
.drop {
  padding: 28px 0;
  color: #606266;
}
.preview {
  margin-top: 20px;
}
.hint {
  color: #606266;
  margin-bottom: 12px;
}
.create {
  margin-top: 16px;
}
</style>
