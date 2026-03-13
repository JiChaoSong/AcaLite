<script setup lang="ts">
import axios from 'axios'
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
  } catch (error: unknown) {
    message.value = '上传或分析失败，请检查后端服务状态。'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section>
    <h2>本地文献导入（PDF / CAJ）</h2>
    <input type="file" accept=".pdf,.caj,application/pdf" @change="uploadFile" />
    <p>{{ loading ? '处理中...' : message }}</p>

    <div v-if="analysis" style="background: #f7f8fa; border-radius: 8px; padding: 12px; margin-top: 12px;">
      <h3>AI 文献分析结果</h3>
      <p><b>精简摘要：</b>{{ analysis.concise_summary }}</p>
      <p><b>核心观点：</b></p>
      <ul>
        <li v-for="(point, index) in analysis.core_points" :key="index">{{ point }}</li>
      </ul>
      <p><b>研究方法：</b>{{ analysis.research_method }}</p>
      <p><b>结论：</b>{{ analysis.conclusion }}</p>
      <p><b>中文翻译：</b>{{ analysis.translations.summary_zh }}</p>
      <p><b>英文翻译：</b>{{ analysis.translations.summary_en }}</p>

      <p><b>文献思维导图（Mermaid）：</b></p>
      <pre style="white-space: pre-wrap;">{{ analysis.mindmap_markdown }}</pre>
    </div>
  </section>
</template>
