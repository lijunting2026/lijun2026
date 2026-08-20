<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"

interface TabItem {
  label: string
  route: string
}

const route = useRoute()
const router = useRouter()

const tabs = computed(() => (route.meta?.tabs as TabItem[]) || [])

const activeTab = computed(() => {
  const sorted = [...tabs.value].sort((a, b) => b.route.length - a.route.length)
  const matched = sorted.find((t) => route.path.startsWith(t.route))
  return matched ? matched.route : tabs.value[0]?.route || ""
})

function handleTabClick(tab: { props: { name: string } }) {
  router.push(tab.props.name)
}
</script>

<template>
  <div class="tab-group-wrapper">
    <div style="padding:4px 12px;background:#fff3cd;border:1px solid #ffeeba;border-radius:4px;margin-bottom:4px;font-size:12px;color:#856404">
      标签数量: <strong>{{ tabs.length }}</strong>
      <span v-if="tabs.length"> | 标签: <span v-for="(t,i) in tabs" :key="i" style="margin-right:6px">{{ t.label }}</span></span>
      <span v-else style="color:red"> ❌ 未找到标签数据!</span>
    </div>
    <div class="tab-card">
      <el-tabs
        :model-value="activeTab"
        class="tab-group-header"
        @tab-click="handleTabClick"
      >
        <el-tab-pane
          v-for="tab in tabs"
          :key="tab.route"
          :label="tab.label"
          :name="tab.route"
        />
      </el-tabs>
    </div>
    <div class="tab-group-content">
      <router-view />
    </div>
  </div>
</template>

<style scoped>
.tab-group-wrapper {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 12px;
}
.tab-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 0 8px;
}
.tab-group-header {
  padding: 0;
}
.tab-group-content {
  flex: 1;
}
:deep(.el-tabs__header) {
  margin-bottom: 0;
}
:deep(.el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.el-tabs__item) {
  font-size: 14px;
  font-weight: 500;
  height: 44px;
  line-height: 44px;
  padding: 0 20px;
}
</style>