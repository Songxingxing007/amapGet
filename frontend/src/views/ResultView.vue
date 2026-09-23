<template>
  <div>
    <el-card shadow="never" class="block">
      <template #header>任务进度</template>
      <TaskProgress :task-id="taskId" />
    </el-card>
    <el-card shadow="never" class="block">
      <template #header>候选与筛选</template>
      <RecordTable :task-id="taskId" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import RecordTable from '@/components/RecordTable.vue'
import TaskProgress from '@/components/TaskProgress.vue'

const route = useRoute()
const taskId = computed(() => Number(route.params.taskId ?? 0))
</script>

<style scoped>
.block {
  margin-bottom: 16px;
}
</style>
