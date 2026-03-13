<script setup lang="ts">
import axios from 'axios'
import { onMounted, ref } from 'vue'

type ModelProvider = 'local' | 'openai-compatible'

const provider = ref<ModelProvider>('local')
const localModelBaseUrl = ref('http://localhost:11434')
const openaiBaseUrl = ref('https://api.openai.com/v1')
const apiKey = ref('')
const message = ref('')
const checking = ref(false)
const backendStatus = ref('unknown')

function resetSettings() {
  provider.value = 'local'
  localModelBaseUrl.value = 'http://localhost:11434'
  openaiBaseUrl.value = 'https://api.openai.com/v1'
  apiKey.value = ''
  message.value = '已恢复默认设置，请点击保存。'
}

onMounted(() => {
  provider.value = (localStorage.getItem('model_provider') as ModelProvider) || 'local'
  localModelBaseUrl.value = localStorage.getItem('local_model_base_url') || localModelBaseUrl.value
  openaiBaseUrl.value = localStorage.getItem('openai_base_url') || openaiBaseUrl.value
  apiKey.value = localStorage.getItem('openai_api_key') || ''
})

async function checkBackend() {
  checking.value = true
  try {
    const res = await axios.get('http://localhost:8000/api/v1/health')
    backendStatus.value = res.data.status === 'ok' ? 'online' : 'unknown'
  } catch {
    backendStatus.value = 'offline'
  } finally {
    checking.value = false
  }
}

function saveSettings() {
  localStorage.setItem('model_provider', provider.value)
  localStorage.setItem('local_model_base_url', localModelBaseUrl.value)
  localStorage.setItem('openai_base_url', openaiBaseUrl.value)
  localStorage.setItem('openai_api_key', apiKey.value)
  message.value = '设置已保存（当前为本地存储，后续将对接后端）。'
}
</script>

<template>
  <el-card shadow="hover" style="border-radius:14px; max-width: 840px;">
    <template #header>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong>设置中心</strong>
        <el-tag :type="backendStatus === 'online' ? 'success' : backendStatus === 'offline' ? 'danger' : 'info'">
          后端状态：{{ backendStatus }}
        </el-tag>
      </div>
    </template>
    <el-alert title="用于配置模型供应商、本地模型地址和 API Key（MVP 先存储在浏览器本地）。" type="info" :closable="false" show-icon />

    <el-form label-width="160px" style="margin-top: 16px;">
      <el-form-item label="模型供应商">
        <el-radio-group v-model="provider">
          <el-radio label="local">本地模型（默认）</el-radio>
          <el-radio label="openai-compatible">OpenAI 兼容 API</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item label="本地模型地址">
        <el-input v-model="localModelBaseUrl" placeholder="http://localhost:11434" />
      </el-form-item>

      <el-form-item label="OpenAI Base URL">
        <el-input v-model="openaiBaseUrl" placeholder="https://api.openai.com/v1" />
      </el-form-item>

      <el-form-item label="API Key">
        <el-input v-model="apiKey" type="password" show-password placeholder="sk-..." />
      </el-form-item>

      <el-form-item>
        <el-space>
          <el-button type="primary" @click="saveSettings">保存设置</el-button>
          <el-button @click="resetSettings">恢复默认</el-button>
          <el-button :loading="checking" @click="checkBackend">检测后端连接</el-button>
        </el-space>
      </el-form-item>
    </el-form>

    <el-alert v-if="message" :title="message" type="success" show-icon :closable="false" />
  </el-card>
</template>
