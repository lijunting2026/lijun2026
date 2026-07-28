<script setup lang="ts">
import { useRouter } from "vue-router"
const router = useRouter()
</script>

<template>
  <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 60vh">
    <h1 style="font-size: 72px; color: #dcdfe6; margin: 0">404</h1>
    <p style="color: #909399; font-size: 16px; margin: 12px 0 24px">页面不存在</p>
    <el-button type="primary" @click="router.push('/dashboard')">返回首页</el-button>
  </div>
</template>