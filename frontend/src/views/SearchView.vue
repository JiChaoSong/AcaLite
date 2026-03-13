<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

const query = ref('')
const results = ref<Array<{title:string; snippet:string; page_no:number}>>([])

async function search() {
  const res = await axios.post('http://localhost:8000/api/v1/retrieval/search', { query: query.value })
  results.value = res.data
}
</script>

<template>
  <section>
    <h2>检索</h2>
    <input v-model="query" placeholder="输入关键词" />
    <button @click="search">搜索</button>
    <ul>
      <li v-for="(item, idx) in results" :key="idx">
        <strong>{{ item.title }}</strong> - p{{ item.page_no }}<br />
        {{ item.snippet }}
      </li>
    </ul>
  </section>
</template>
