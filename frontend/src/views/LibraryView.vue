<script setup lang="ts">
import axios from 'axios'
import { DocumentCopy, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

type AnalysisPayload = {
  concise_summary: string
  core_points: string[]
  research_method: string
  conclusion: string
  translations: { summary_zh: string; summary_en: string }
  mindmap_markdown: string
}

type DocumentItem = { id: number; title: string; file_path: string; created_at: string | null }

const message = ref('')
const loading = ref(false)
const analysis = ref<AnalysisPayload | null>(null)
const recentDocs = ref<DocumentItem[]>([])

async function loadRecentDocs() {
  const res = await axios.get('http://localhost:8000/api/v1/documents', { params: { limit: 8 } })
  recentDocs.value = res.data
}

async function analyzeDocument(documentId: number) {
  loading.value = true
  try {
    const analysisRes = await axios.post(`http://localhost:8000/api/v1/ai/analyze/${documentId}`)
    analysis.value = analysisRes.data
    ElMessage.success('文献分析完成')
  } finally {
    loading.value = false
  }
}

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
    await analyzeDocument(importRes.data.id)
    message.value = `导入并分析成功: ${importRes.data.title} (id=${importRes.data.id})`
    await loadRecentDocs()
  } catch {
    message.value = '上传或分析失败，请检查后端服务状态。'
  } finally {
    loading.value = false
  }
}

function copySummary() {
  if (!analysis.value) return
  navigator.clipboard.writeText(analysis.value.concise_summary)
  ElMessage.success('精简摘要已复制')
}

onMounted(loadRecentDocs)
</script>

<template>
  <el-space direction="vertical" fill :size="14" style="width:100%;">
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
    </el-card>

    <el-card shadow="never" style="border-radius: 14px;">
      <template #header><strong>最近导入文献</strong></template>
      <el-table :data="recentDocs" size="small" empty-text="暂无导入记录">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="created_at" label="导入时间" width="220" />
        <el-table-column label="操作" width="130">
          <template #default="scope">
            <el-button text type="primary" @click="analyzeDocument(scope.row.id)">分析</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card v-if="analysis" style="background: #fafcff; border-radius: 14px;" shadow="never">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <strong>AI 文献分析结果</strong>
          <el-button :icon="DocumentCopy" plain @click="copySummary">复制摘要</el-button>
        </div>
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
        <el-tag v-for="(point, index) in analysis.core_points" :key="index" style="margin: 8px 8px 0 0;" effect="plain">{{ point }}</el-tag>
      </div>

      <div style="margin-top:12px;">
        <strong>文献思维导图（Mermaid）</strong>
        <el-input type="textarea" :rows="8" :model-value="analysis.mindmap_markdown" readonly />
      </div>
    </el-card>
  </el-space>
</template>
