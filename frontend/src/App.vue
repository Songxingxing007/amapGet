<template>
  <el-container class="app">
    <el-header class="bar">
      <div class="brand">高德 POI / AOI 采集工具</div>
      <el-menu mode="horizontal" :default-active="active" router :ellipsis="false">
        <el-menu-item index="/config">配置</el-menu-item>
        <el-menu-item index="/upload">上传</el-menu-item>
        <el-menu-item index="/result">结果</el-menu-item>
      </el-menu>
      <el-tag class="status" :type="tagType">{{ status }}</el-tag>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const status = ref('检测中')

const active = computed(() => (route.path.startsWith('/result') ? '/result' : route.path))
const tagType = computed(() => (status.value === 'ok' ? 'success' : 'info'))

onMounted(async () => {
  try {
    const resp = await fetch('/api/health')
    const data = (await resp.json()) as { status?: string }
    status.value = data.status ?? '未知'
  } catch {
    status.value = '未连通'
  }
})
</script>

<style scoped>
.app {
  padding: 0 0 24px;
}
.bar {
  display: flex;
  align-items: center;
  gap: 24px;
  border-bottom: 1px solid #ebeef5;
  background: #fff;
}
.brand {
  font-size: 16px;
  font-weight: 600;
}
.status {
  margin-left: auto;
}
</style>
