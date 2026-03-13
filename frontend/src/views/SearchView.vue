<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

type SearchResult = {
  document_id: number
  title: string
  snippet: string
  page_no: number
}

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

type CitationPayload = {
  style: string
  formatted_text: string
  bibtex: string
}

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
  } catch (error) {
    errorMessage.value = '检索失败，请确认后端已启动。'
  } finally {
    loading.value = false
  }
}

function toggleDoc(documentId: number) {
  if (selectedDocIds.value.includes(documentId)) {
    selectedDocIds.value = selectedDocIds.value.filter((id) => id !== documentId)
  } else {
    selectedDocIds.value = [...selectedDocIds.value, documentId]
  }
}

async function generateAnalysis(documentId: number) {
  const res = await axios.post(`http://localhost:8000/api/v1/ai/analyze/${documentId}`)
  analyses.value = { ...analyses.value, [documentId]: res.data }
}

async function generateCitation(documentId: number, style: CitationStyle) {
  const res = await axios.post('http://localhost:8000/api/v1/citations/generate', {
    document_id: documentId,
    style
  })
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
  const filename = `${title.replace(/\s+/g, '_') || 'citation'}.bib`

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}
</script>

<template>
  <section>
    <h2>检索</h2>
    <div style="display: flex; gap: 8px; margin-bottom: 12px;">
      <input v-model="query" placeholder="输入关键词" @keyup.enter="search" />
      <button @click="search" :disabled="loading">{{ loading ? '搜索中...' : '搜索' }}</button>
    </div>

    <div style="display:flex; gap:8px; align-items:center; margin-bottom: 12px;">
      <label>参考文献格式</label>
      <select v-model="referenceStyle">
        <option value="apa">APA</option>
        <option value="mla">MLA</option>
        <option value="gbt7714">GB/T 7714</option>
      </select>
      <button @click="generateReferenceList">一键生成参考文献列表</button>
    </div>

    <pre v-if="referenceListText" style="white-space: pre-wrap; background:#f4f8ff; padding:8px; border-radius:4px;">{{ referenceListText }}</pre>

    <p v-if="errorMessage" style="color: #d33;">{{ errorMessage }}</p>

    <ul style="padding-left: 18px; display: grid; gap: 16px;">
      <li v-for="item in results" :key="`${item.document_id}-${item.page_no}`">
        <label style="display:flex; gap:8px; align-items:center;">
          <input type="checkbox" :checked="selectedDocIds.includes(item.document_id)" @change="toggleDoc(item.document_id)" />
          <strong>{{ item.title }}</strong> - p{{ item.page_no }}
        </label>
        <p style="margin: 8px 0;">{{ item.snippet }}</p>

        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 8px;">
          <button @click="generateAnalysis(item.document_id)">AI 分析</button>
          <button @click="generateCitation(item.document_id, 'apa')">APA 引用</button>
          <button @click="generateCitation(item.document_id, 'mla')">MLA 引用</button>
          <button @click="generateCitation(item.document_id, 'gbt7714')">GB/T 7714 引用</button>
          <button v-if="citations[item.document_id]" @click="downloadBibtex(item.document_id, item.title)">
            导出 .bib
          </button>
        </div>

        <div v-if="analyses[item.document_id]" style="background: #f7f7f7; padding: 8px; border-radius: 4px;">
          <strong>AI 文献分析</strong>
          <p><b>精简摘要:</b> {{ analyses[item.document_id].concise_summary }}</p>
          <p><b>研究方法:</b> {{ analyses[item.document_id].research_method }}</p>
          <p><b>结论:</b> {{ analyses[item.document_id].conclusion }}</p>
          <p><b>中文翻译:</b> {{ analyses[item.document_id].translations.summary_zh }}</p>
          <p><b>英文翻译:</b> {{ analyses[item.document_id].translations.summary_en }}</p>
          <p><b>核心观点:</b></p>
          <ul>
            <li v-for="(point, index) in analyses[item.document_id].core_points" :key="index">{{ point }}</li>
          </ul>
          <pre style="white-space: pre-wrap;">{{ analyses[item.document_id].mindmap_markdown }}</pre>
        </div>

        <div v-if="citations[item.document_id]" style="background: #f4f8ff; padding: 8px; border-radius: 4px; margin-top: 8px;">
          <strong>引用（{{ citations[item.document_id].style.toUpperCase() }}）</strong>
          <p>{{ citations[item.document_id].formatted_text }}</p>
          <pre style="white-space: pre-wrap;">{{ citations[item.document_id].bibtex }}</pre>
        </div>
      </li>
    </ul>
  </section>
</template>
