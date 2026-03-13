<script setup lang="ts">
import axios from 'axios'
import { ref } from 'vue'

const message = ref('')

async function uploadFile(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files || !input.files.length) return
  const file = input.files[0]
  const form = new FormData()
  form.append('file', file)
  const res = await axios.post('http://localhost:8000/api/v1/documents/import', form)
  message.value = `导入成功: ${res.data.title} (id=${res.data.id})`
}
</script>

<template>
  <section>
    <h2>本地文献导入</h2>
    <input type="file" accept="application/pdf" @change="uploadFile" />
    <p>{{ message }}</p>
  </section>
</template>
