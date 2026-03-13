<script setup lang="ts">
import { onMounted, ref } from 'vue'

type ModelProvider = 'local' | 'openai-compatible'

const provider = ref<ModelProvider>('local')
const localModelBaseUrl = ref('http://localhost:11434')
const openaiBaseUrl = ref('https://api.openai.com/v1')
const apiKey = ref('')
const message = ref('')

onMounted(() => {
  provider.value = (localStorage.getItem('model_provider') as ModelProvider) || 'local'
  localModelBaseUrl.value = localStorage.getItem('local_model_base_url') || localModelBaseUrl.value
  openaiBaseUrl.value = localStorage.getItem('openai_base_url') || openaiBaseUrl.value
  apiKey.value = localStorage.getItem('openai_api_key') || ''
})

function saveSettings() {
  localStorage.setItem('model_provider', provider.value)
  localStorage.setItem('local_model_base_url', localModelBaseUrl.value)
  localStorage.setItem('openai_base_url', openaiBaseUrl.value)
  localStorage.setItem('openai_api_key', apiKey.value)
  message.value = '设置已保存（当前为本地存储，后续将对接后端）。'
}
</script>

<template>
  <section>
    <h2>设置</h2>
    <p>用于配置模型供应商、本地模型地址和 API Key（MVP 先存储在浏览器本地）。</p>

    <div style="display: grid; gap: 12px; max-width: 600px;">
      <label>
        模型供应商
        <select v-model="provider">
          <option value="local">本地模型（默认）</option>
          <option value="openai-compatible">OpenAI 兼容 API</option>
        </select>
      </label>

      <label>
        本地模型地址
        <input v-model="localModelBaseUrl" placeholder="http://localhost:11434" />
      </label>

      <label>
        OpenAI 兼容 Base URL
        <input v-model="openaiBaseUrl" placeholder="https://api.openai.com/v1" />
      </label>

      <label>
        API Key
        <input v-model="apiKey" type="password" placeholder="sk-..." />
      </label>

      <button @click="saveSettings" style="width: fit-content;">保存设置</button>
      <p v-if="message" style="color: #0a7a25;">{{ message }}</p>
    </div>
  </section>
</template>
