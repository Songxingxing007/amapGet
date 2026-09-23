<template>
  <el-card shadow="never">
    <template #header>接口配置</template>
    <el-form label-width="160px" @submit.prevent>
      <el-form-item label="高德 API Key">
        <div class="key-list">
          <div v-for="(_, index) in form.keys" :key="index" class="key-row">
            <el-input
              v-model="form.keys[index]"
              type="password"
              show-password
              placeholder="Web 服务 Key"
              data-test="key-input"
            />
            <el-button :disabled="form.keys.length <= 1" @click="removeKey(index)">删除</el-button>
          </div>
        </div>
        <el-button class="add-key" @click="addKey">添加 Key</el-button>
        <div v-if="savedMasked.length" class="hint">已保存：{{ savedMasked.join('、') }}</div>
      </el-form-item>
      <el-form-item label="QPS 上限">
        <el-input-number v-model="form.qps" :min="0.1" :max="50" :step="0.5" />
      </el-form-item>
      <el-form-item label="单 Key 日上限">
        <el-input-number v-model="form.daily_limit_per_key" :min="1" :step="100" />
      </el-form-item>
      <el-form-item label="默认城市 adcode">
        <el-input v-model="form.default_region" style="width: 220px" />
      </el-form-item>
      <el-form-item label="每个名称最多取多少条 POI">
        <el-input-number v-model="form.poi_page_size" :min="1" :max="25" />
        <span class="sep">条/页</span>
        <el-input-number v-model="form.poi_max_pages" :min="1" :max="8" />
        <span class="sep">页</span>
      </el-form-item>
      <el-form-item label="分类码前缀过滤">
        <el-input v-model="form.typecode_prefix" style="width: 220px" placeholder="留空则不过滤" />
        <div class="hint">11 = 风景名胜类（公园广场、景区）；留空会把地铁站、停车场也收进来</div>
      </el-form-item>
      <el-form-item label="每 N 次请求休息">
        <el-input-number v-model="form.sleep_every" :min="0" />
      </el-form-item>
      <el-form-item label="休息区间（秒）">
        <el-input-number v-model="form.sleep_min_seconds" :min="0" :step="0.5" />
        <span class="sep">~</span>
        <el-input-number v-model="form.sleep_max_seconds" :min="0" :step="0.5" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="save">保存配置</el-button>
        <el-button :loading="verifying" @click="verify">测试接口</el-button>
      </el-form-item>
    </el-form>
    <el-alert
      v-if="verifyResult"
      :type="verifyResult.aoi_status === 'ok' ? 'success' : 'warning'"
      :closable="false"
      show-icon
    >
      <p>Key：{{ verifyResult.key_message }}（{{ verifyResult.key_masked }}）</p>
      <p>地理编码：{{ verifyResult.geocode_location || '未返回坐标' }}</p>
      <p>AOI：{{ verifyResult.aoi_message }}</p>
      <p v-if="verifyResult.aoi_hint" class="hint">{{ verifyResult.aoi_hint }}</p>
    </el-alert>
  </el-card>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { getConfig, putConfig, verifyConfig } from '@/api/client'
import type { ConfigPayload, VerifyResult } from '@/api/types'

type RequiredConfig = Required<ConfigPayload>

const form = reactive<RequiredConfig>({
  keys: [''],
  qps: 3,
  daily_limit_per_key: 4500,
  default_region: '440100',
  sleep_every: 20,
  sleep_min_seconds: 3,
  sleep_max_seconds: 8,
  poi_page_size: 25,
  poi_max_pages: 1,
  typecode_prefix: '11',
})
const savedMasked = ref<string[]>([])
const saving = ref(false)
const verifying = ref(false)
const verifyResult = ref<VerifyResult | null>(null)

function addKey() {
  form.keys.push('')
}

function removeKey(index: number) {
  form.keys.splice(index, 1)
}

function cleanedKeys(): string[] {
  return form.keys.map((k) => k.trim()).filter((k) => k.length > 0)
}

async function load() {
  try {
    const cfg = await getConfig()
    savedMasked.value = cfg.keys_masked
    form.qps = cfg.qps
    form.daily_limit_per_key = cfg.daily_limit_per_key
    form.default_region = cfg.default_region
    form.sleep_every = cfg.sleep_every
    form.sleep_min_seconds = cfg.sleep_min_seconds
    form.sleep_max_seconds = cfg.sleep_max_seconds
  } catch {
    // first run: nothing saved yet
  }
}

async function save() {
  const keys = cleanedKeys()
  if (!keys.length) {
    ElMessage.warning('至少填一个 Key')
    return
  }
  saving.value = true
  try {
    const cfg = await putConfig({ ...form, keys })
    savedMasked.value = cfg.keys_masked
    ElMessage.success(`已保存 ${cfg.key_count} 个 Key`)
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    saving.value = false
  }
}

async function verify() {
  verifying.value = true
  try {
    verifyResult.value = await verifyConfig()
  } catch (error) {
    ElMessage.error((error as Error).message)
  } finally {
    verifying.value = false
  }
}

onMounted(load)
defineExpose({ form, savedMasked, verifyResult, save, verify, cleanedKeys, addKey, removeKey })
</script>

<style scoped>
.key-list {
  width: 100%;
}
.key-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  max-width: 520px;
}
.add-key {
  margin-top: 4px;
}
.hint {
  color: #909399;
  font-size: 12px;
}
.sep {
  margin: 0 8px;
  color: #909399;
}
</style>
