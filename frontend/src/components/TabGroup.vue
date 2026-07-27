<script setup lang="ts">
import { computed } from "vue"
import { useRoute, useRouter } from "vue-router"

interface TabItem {
  label: string
  route: string
}

const props = defineProps<{
  tabs: TabItem[]
}>()

const route = useRoute()
const router = useRouter()

const activeTab = computed(() => {
  const sorted = [...props.tabs].sort((a, b) => b.route.length - a.route.length)
  const matched = sorted.find((t) => route.path.startsWith(t.route))
  return matched ? matched.route : props.tabs[0]?.route || ""
})

function handleTabClick(tab: { props: { name: string } }) {
  router.push(tab.props.name)
}
</script>

<template>
  <div class="tab-group-wrapper">
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
