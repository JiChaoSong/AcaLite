<script setup lang="ts">
import axios from 'axios'
import { UploadFilled } from '@element-plus/icons-vue'
import { ref } from 'vue'

type AnalysisPayload = {
  concise_summary: string
  core_points: string[]
  research_method: string
  conclusion: string
  translations: {
    summary_zh: string
    summary_en: string
  }
  mindmap_markdown: string
}

const message = ref('')
const loading = ref(false)
const analysis = ref<AnalysisPayload | null>(null)

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files.length) return

  const file = input.files[0]
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!ext || !['pdf', 'caj'].includes(ext)) {
    message.value = '仅支持上传 PDF 或 CAJ 文件。'
    return
  }

  loading.value = true
  analysis.value = null
  try {
    const form = new FormData()
    form.append('file', file)
    const importRes = await axios.post('http://localhost:8000/api/v1/documents/import', form)
    const analysisRes = await axios.post(`http://localhost:8000/api/v1/ai/analyze/${importRes.data.id}`)

    message.value = `导入并分析成功: ${importRes.data.title} (id=${importRes.data.id})`
    analysis.value = analysisRes.data
  } catch {
    message.value = '上传或分析失败，请检查后端服务状态。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-card shadow="hover" style="border-radius: 14px;">
    <template #header>
      <div style="display:flex; justify-content:space-between; align-items:center;">
        <span style="font-weight:600;">本地文献导入（PDF / CAJ）</span>
        <el-tag type="success">自动AI分析</el-tag>
      </div>
    </template>

    <el-space direction="vertical" fill :size="14">
      <input id="doc-upload" type="file" accept=".pdf,.caj,application/pdf" style="display:none" @change="uploadFile" />
      <label for="doc-upload">
        <el-button type="primary" :loading="loading" :icon="UploadFilled">选择并上传文件</el-button>
      </label>
      <el-alert v-if="message" :title="message" :type="message.includes('失败') ? 'error' : 'success'" show-icon :closable="false" />
    </el-space>

    <el-card v-if="analysis" style="margin-top: 16px; background: #fafcff;" shadow="never">
      <template #header>
        <strong>AI 文献分析结果</strong>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="精简摘要">{{ analysis.concise_summary }}</el-descriptions-item>
        <el-descriptions-item label="研究方法">{{ analysis.research_method }}</el-descriptions-item>
        <el-descriptions-item label="结论">{{ analysis.conclusion }}</el-descriptions-item>
        <el-descriptions-item label="中文翻译">{{ analysis.translations.summary_zh }}</el-descriptions-item>
        <el-descriptions-item label="英文翻译">{{ analysis.translations.summary_en }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top:12px;">
        <strong>核心观点</strong>
        <el-tag v-for="(point, index) in analysis.core_points" :key="index" style="margin: 8px 8px 0 0;" effect="plain">
          {{ point }}
        </el-tag>
      </div>

      <div style="margin-top:12px;">
        <strong>文献思维导图（Mermaid）</strong>
        <el-input type="textarea" :rows="8" :model-value="analysis.mindmap_markdown" readonly />
      </div>
    </el-card>
  </el-card>
</template>
