<script setup lang="ts">
import { useAuthStore } from "@/stores"
import { useRouter, useRoute } from "vue-router"
import { ref, computed, onMounted, onUnmounted } from "vue"

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

function handleKeydown(e: KeyboardEvent) {
  if (e.ctrlKey && e.key === "k") {
    e.preventDefault()
    router.push("/students-group/students")
  }
}
onMounted(() => window.addEventListener("keydown", handleKeydown))
onUnmounted(() => window.removeEventListener("keydown", handleKeydown))

function handleLogout() {
  auth.logout()
  router.push("/login")
}

const breadcrumb = computed(() => {
  const path = route.path
  const meta = route.meta as any
  // Map parent routes to parent labels from router config
  const parents: Record<string, { label: string; defaultChild: string }> = {
    "/students-group": { label: "学生与班级管理", defaultChild: "/students-group/schools" },
    "/exam-group": { label: "考试与科目管理", defaultChild: "/exam-group/subjects" },
    "/analysis-group": { label: "数据分析与跟踪", defaultChild: "/analysis-group/analysis" },
  }
  for (const [parentPath, info] of Object.entries(parents)) {
    if (path.startsWith(parentPath)) {
      return { parent: info.label, parentLink: info.defaultChild, child: meta?.title || "" }
    }
  }
  return { parent: "", parentLink: "", child: meta?.title || "" }
})
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-aside">
      <div class="logo">
        <el-icon :size="22" color="#409EFF"><Platform /></el-icon>
        <span v-show="!sidebarCollapsed" class="logo-text">考试质量分析系统</span>
      </div>
      <div class="sidebar-toggle" @click="toggleSidebar">
        <el-icon :size="18">
          <Fold v-if="!sidebarCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
      <el-menu
        :default-active="route.path"
        router
        :collapse="sidebarCollapsed"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#ffffff"
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-sub-menu index="/students-group">
          <template #title>
            <el-icon><UserFilled /></el-icon>
            <span>学生与班级</span>
          </template>
          <el-menu-item index="/students-group/schools">年级班级</el-menu-item>
          <el-menu-item index="/students-group/students">学生管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/exam-group">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>考试与科目</span>
          </template>
          <el-menu-item index="/exam-group/subjects">科目管理</el-menu-item>
          <el-menu-item index="/exam-group/exams">考试管理</el-menu-item>
          <el-menu-item index="/exam-group/scores">成绩管理</el-menu-item>
        </el-sub-menu>
        <el-sub-menu index="/analysis-group">
          <template #title>
            <el-icon><TrendCharts /></el-icon>
            <span>数据分析</span>
          </template>
          <el-menu-item index="/analysis-group/analysis">年级分析</el-menu-item>
          <el-menu-item index="/analysis-group/class-analysis">班级分析</el-menu-item>
          <el-menu-item index="/analysis-group/student-tracking">个体分析</el-menu-item>
        </el-sub-menu>
        <el-menu-item index="/users" v-if="auth.isAdmin">
          <el-icon><Setting /></el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item v-if="breadcrumb.parent" :to="breadcrumb.parentLink">
              {{ breadcrumb.parent }}
            </el-breadcrumb-item>
            <el-breadcrumb-item>{{ breadcrumb.child }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <el-dropdown trigger="click" @command="handleLogout">
          <span class="user-info">
            <el-icon color="#409EFF"><User /></el-icon>
            <span class="user-name">{{ auth.displayName }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-item command="logout">
              <el-icon><SwitchButton /></el-icon>退出登录
            </el-dropdown-item>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="app-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-aside {
  background-color: #001529;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}
.logo {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}
.logo-text {
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}
.sidebar-toggle {
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.65);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  transition: color 0.2s;
}
.sidebar-toggle:hover {
  color: #fff;
}
.el-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
  height: 56px !important;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #606266;
  padding: 6px 12px;
  border-radius: 6px;
  transition: background 0.2s;
}
.user-info:hover {
  background: #f5f7fa;
}
.user-name {
  font-size: 14px;
  font-weight: 500;
}
.app-main {
  background-color: #f0f2f5;
  overflow-y: auto;
  padding: 16px !important;
}
@media (max-width: 768px) {
  .app-aside {
    position: fixed;
    z-index: 1000;
    height: 100vh;
  }
  .app-header { padding: 0 12px; }
  .app-main { padding: 12px !important; }
}

/* Page transition animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}
</style>
