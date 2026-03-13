<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()
const activeMenu = ref(route.path)

watch(
  () => route.path,
  (path) => {
    activeMenu.value = path
  }
)

function onSelect(index: string) {
  router.push(index)
}
</script>

<template>
  <el-container style="min-height: 100vh; background: linear-gradient(180deg, #f5f8ff 0%, #f7fbf8 100%);">
    <el-header style="height: auto; padding: 16px 24px 8px;">
      <el-card shadow="never" style="border-radius: 14px;">
        <div style="display:flex; justify-content:space-between; align-items:center; gap:16px; flex-wrap:wrap;">
          <div>
            <h1 style="margin:0; font-size: 24px; color:#1f2d3d;">AcaLite MVP</h1>
            <p style="margin:6px 0 0; color:#64748b;">本地优先的 AI 学术阅读与写作助手</p>
          </div>
          <el-menu mode="horizontal" :default-active="activeMenu" @select="onSelect" style="border-bottom:none;">
            <el-menu-item index="/">文献导入</el-menu-item>
            <el-menu-item index="/search">检索与引用</el-menu-item>
            <el-menu-item index="/settings">设置</el-menu-item>
          </el-menu>
        </div>
      </el-card>
    </el-header>

    <el-main style="padding: 12px 24px 24px; max-width: 1200px; width: 100%; margin: 0 auto;">
      <RouterView />
    </el-main>
  </el-container>
</template>
