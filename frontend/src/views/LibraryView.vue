<script setup lang="ts">
import axios from 'axios'
import { DocumentCopy, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import type { UploadRequestOptions } from 'element-plus'
import { onMounted, ref } from 'vue'

type AnalysisPayload = {
  concise_summary: string
  core_points: string[]
  research_method: string
  conclusion: string
  translations: { summary_zh: string; summary_en: string }
  mindmap_markdown: string
  engine?: string
}

type DocumentItem = { id: number; title: string; file_path: string; created_at: string | null }

const message = ref('')
const loading = ref(false)
const analysis = ref<AnalysisPayload | null>(null)
const recentDocs = ref<DocumentItem[]>([])
const importStep = ref<'idle' | 'uploading' | 'analyzing'>('idle')

async function loadRecentDocs() {
  const res = await axios.get('http://localhost:8000/api/v1/documents', { params: { limit: 8 } })
  recentDocs.value = res.data
}

async function analyzeDocument(documentId: number) {
  importStep.value = 'analyzing'
  const analysisRes = await axios.post(`http://localhost:8000/api/v1/ai/analyze/${documentId}`)
  analysis.value = analysisRes.data
  ElMessage.success('文献分析完成')
}

async function handleUpload(options: UploadRequestOptions) {
  const file = options.file as File
  const ext = file.name.split('.').pop()?.toLowerCase()
  if (!ext || !['pdf', 'caj'].includes(ext)) {
    const error = new Error('仅支持上传 PDF 或 CAJ 文件')
    options.onError(error)
    ElMessage.error(error.message)
    return
  }

  loading.value = true
  importStep.value = 'uploading'
  analysis.value = null

  try {
    const form = new FormData()
    form.append('file', file)
    const importRes = await axios.post('http://localhost:8000/api/v1/documents/import', form)
    await analyzeDocument(importRes.data.id)
    await loadRecentDocs()
    message.value = `导入并分析成功: ${importRes.data.title} (id=${importRes.data.id})`
    options.onSuccess(importRes.data)
  } catch (error) {
    message.value = '上传或分析失败，请检查后端服务状态。'
    options.onError(error as Error)
  } finally {
    loading.value = false
    importStep.value = 'idle'
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
        <el-upload :show-file-list="false" :http-request="handleUpload" accept=".pdf,.caj,application/pdf">
          <el-button type="primary" :loading="loading" :icon="UploadFilled">选择并上传文件</el-button>
        </el-upload>

        <el-alert
          v-if="importStep !== 'idle'"
          :title="importStep === 'uploading' ? '正在上传文档...' : '正在调用大模型解析文档并生成结构化分析...'"
          type="info"
          show-icon
          :closable="false"
        />

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
          <el-space>
            <el-tag size="small" type="warning">引擎: {{ analysis.engine || 'heuristic' }}</el-tag>
            <el-button :icon="DocumentCopy" plain @click="copySummary">复制摘要</el-button>
          </el-space>
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
