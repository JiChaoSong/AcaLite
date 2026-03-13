<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

type SearchResult = { document_id: number; title: string; snippet: string; page_no: number }
type AnalysisPayload = {
  concise_summary: string
  core_points: string[]
  research_method: string
  conclusion: string
  translations: { summary_zh: string; summary_en: string }
  mindmap_markdown: string
}
type CitationPayload = { style: string; formatted_text: string; bibtex: string }
type CitationStyle = 'apa' | 'mla' | 'gbt7714'

const query = ref('')
const results = ref<SearchResult[]>([])
const loading = ref(false)
const errorMessage = ref('')
const analyses = ref<Record<number, AnalysisPayload>>({})
const citations = ref<Record<number, CitationPayload>>({})
const selectedDocIds = ref<number[]>([])
const referenceStyle = ref<CitationStyle>('apa')
const referenceListText = ref('')

async function search() {
  if (!query.value.trim()) {
    results.value = []
    selectedDocIds.value = []
    referenceListText.value = ''
    return
  }
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await axios.post('http://localhost:8000/api/v1/retrieval/search', { query: query.value })
    results.value = res.data
  } catch {
    errorMessage.value = '检索失败，请确认后端已启动。'
  } finally {
    loading.value = false
  }
}

function toggleDoc(documentId: number) {
  selectedDocIds.value = selectedDocIds.value.includes(documentId)
    ? selectedDocIds.value.filter((id) => id !== documentId)
    : [...selectedDocIds.value, documentId]
}

async function generateAnalysis(documentId: number) {
  const res = await axios.post(`http://localhost:8000/api/v1/ai/analyze/${documentId}`)
  analyses.value = { ...analyses.value, [documentId]: res.data }
}

async function generateCitation(documentId: number, style: CitationStyle) {
  const res = await axios.post('http://localhost:8000/api/v1/citations/generate', { document_id: documentId, style })
  citations.value = { ...citations.value, [documentId]: res.data }
}

async function generateReferenceList() {
  if (!selectedDocIds.value.length) {
    referenceListText.value = '请先勾选要加入参考文献列表的文献。'
    return
  }
  const res = await axios.post('http://localhost:8000/api/v1/citations/generate-list', {
    document_ids: selectedDocIds.value,
    style: referenceStyle.value
  })
  referenceListText.value = res.data.reference_list
}

function downloadBibtex(documentId: number, title: string) {
  const citation = citations.value[documentId]
  if (!citation) return
  const blob = new Blob([citation.bibtex], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${title.replace(/\s+/g, '_') || 'citation'}.bib`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <el-space direction="vertical" fill :size="14" style="width:100%;">
    <el-card shadow="hover" style="border-radius:14px;">
      <template #header><strong>检索与引用</strong></template>
      <el-row :gutter="12">
        <el-col :span="18"><el-input v-model="query" placeholder="输入关键词" @keyup.enter="search" clearable /></el-col>
        <el-col :span="6"><el-button type="primary" :loading="loading" @click="search" style="width:100%;">搜索</el-button></el-col>
      </el-row>

      <el-space style="margin-top:12px;" wrap>
        <span>参考文献格式</span>
        <el-select v-model="referenceStyle" style="width:160px;">
          <el-option label="APA" value="apa" />
          <el-option label="MLA" value="mla" />
          <el-option label="GB/T 7714" value="gbt7714" />
        </el-select>
        <el-button type="success" @click="generateReferenceList">一键生成参考文献列表</el-button>
      </el-space>

      <el-alert v-if="errorMessage" :title="errorMessage" type="error" show-icon :closable="false" style="margin-top:12px;" />
      <el-input v-if="referenceListText" type="textarea" :rows="4" :model-value="referenceListText" readonly style="margin-top:12px;" />
    </el-card>

    <el-card v-for="item in results" :key="`${item.document_id}-${item.page_no}`" shadow="never" style="border-radius:14px;">
      <template #header>
        <div style="display:flex; justify-content:space-between; align-items:center; gap:8px;">
          <div>
            <el-checkbox :model-value="selectedDocIds.includes(item.document_id)" @change="toggleDoc(item.document_id)">加入文献列表</el-checkbox>
            <strong style="margin-left:8px;">{{ item.title }}</strong>
            <el-tag size="small" style="margin-left:8px;">p{{ item.page_no }}</el-tag>
          </div>
        </div>
      </template>

      <el-text>{{ item.snippet }}</el-text>
      <el-space wrap style="margin-top:10px;">
        <el-button @click="generateAnalysis(item.document_id)">AI 分析</el-button>
        <el-button @click="generateCitation(item.document_id, 'apa')">APA</el-button>
        <el-button @click="generateCitation(item.document_id, 'mla')">MLA</el-button>
        <el-button @click="generateCitation(item.document_id, 'gbt7714')">GB/T 7714</el-button>
        <el-button v-if="citations[item.document_id]" type="primary" plain @click="downloadBibtex(item.document_id, item.title)">
          导出 .bib
        </el-button>
      </el-space>

      <el-collapse style="margin-top:12px;">
        <el-collapse-item v-if="analyses[item.document_id]" title="AI 文献分析" name="analysis">
          <el-descriptions :column="1" border>
            <el-descriptions-item label="精简摘要">{{ analyses[item.document_id].concise_summary }}</el-descriptions-item>
            <el-descriptions-item label="研究方法">{{ analyses[item.document_id].research_method }}</el-descriptions-item>
            <el-descriptions-item label="结论">{{ analyses[item.document_id].conclusion }}</el-descriptions-item>
            <el-descriptions-item label="中文翻译">{{ analyses[item.document_id].translations.summary_zh }}</el-descriptions-item>
            <el-descriptions-item label="英文翻译">{{ analyses[item.document_id].translations.summary_en }}</el-descriptions-item>
          </el-descriptions>
          <el-input type="textarea" :rows="6" :model-value="analyses[item.document_id].mindmap_markdown" readonly style="margin-top:8px;" />
        </el-collapse-item>

        <el-collapse-item v-if="citations[item.document_id]" title="引用结果" name="citation">
          <el-tag type="info">{{ citations[item.document_id].style.toUpperCase() }}</el-tag>
          <p>{{ citations[item.document_id].formatted_text }}</p>
          <el-input type="textarea" :rows="4" :model-value="citations[item.document_id].bibtex" readonly />
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </el-space>
</template>
