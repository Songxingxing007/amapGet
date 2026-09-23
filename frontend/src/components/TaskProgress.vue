<template>
  <div v-if="task">
    <el-progress :percentage="percent" :status="task.status === 'failed' ? 'exception' : undefined" />
    <el-descriptions :column="4" size="small" class="stats">
      <el-descriptions-item label="状态">{{ task.status }}</el-descriptions-item>
      <el-descriptions-item label="总数">{{ task.total }}</el-descriptions-item>
      <el-descriptions-item label="已完成">{{ task.done }}</el-descriptions-item>
      <el-descriptions-item label="失败">{{ task.failed }}</el-descriptions-item>
    </el-descriptions>
    <el-alert v-if="task.paused_reason" type="warning" :closable="false" :title="task.paused_reason" />
    <div class="actions">
      <el-button type="primary" size="small" :loading="starting" @click="startRun">开始采集</el-button>
      <el-button size="small" @click="pauseRun" :disabled="task.status !== 'running'">暂停</el-button>
      <el-button size="small" @click="resumeRun" :disabled="task.status !== 'paused'">继续</el-button>
    </div>
  </div>
  <el-empty v-else description="没有找到任务，先去上传页创建" />
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import { getTask, pauseTask, resumeTask, runTask } from '@/api/client'
import type { TaskView } from '@/api/types'

const props = defineProps<{ taskId: number }>()
const task = ref<TaskView | null>(null)
const starting = ref(false)
let timer: number | null = null

const terminal = new Set(['done', 'failed'])
const percent = computed(() => {
  if (!task.value || task.value.total === 0) return 0
  return Math.min(100, Math.round((task.value.done / task.value.total) * 100))
})

async function refresh() {
  if (!props.taskId) return
  try {
    task.value = await getTask(props.taskId)
  } catch {
    task.value = null
  }
  if (task.value && terminal.has(task.value.status)) {
    stop()
  }
}

function stop() {
  if (timer !== null) {
    window.clearInterval(timer)
    timer = null
  }
}

function start() {
  stop()
  if (!props.taskId) return
  void refresh()
  timer = window.setInterval(refresh, 2000)
}

async function startRun() {
  starting.value = true
  try {
    const result = await runTask(props.taskId)
    ElMessage.success(`已开始采集，待处理 ${result.pending} 条`)
    start()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    starting.value = false
  }
}

async function pauseRun() {
  try {
    task.value = await pauseTask(props.taskId)
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

async function resumeRun() {
  try {
    task.value = await resumeTask(props.taskId)
    start()
  } catch (error) {
    ElMessage.error((error as Error).message)
  }
}

watch(() => props.taskId, start, { immediate: true })
onBeforeUnmount(stop)

defineExpose({ task, percent, refresh, start, stop, startRun, pauseRun, resumeRun })
</script>

<style scoped>
.stats {
  margin-top: 12px;
}
.actions {
  margin-top: 12px;
}
</style>
