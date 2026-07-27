<script setup lang="ts">
import { useAuthStore } from "@/stores"

const auth = useAuthStore()
</script>

<template>
  <router-view v-slot="{ Component }">
    <transition name="fade-slide" mode="out-in">
      <component :is="Component" />
    </transition>
  </router-view>
</template>
<style>
/* Page transition */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.25s ease;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-12px);
}

/* Skeleton loading animation */
@keyframes shimmer {
  0% { background-position: -200px 0; }
  100% { background-position: calc(200px + 100%) 0; }
}
.skeleton {
  background: linear-gradient(90deg, #f0f2f5 25%, #e8eaed 37%, #f0f2f5 63%);
  background-size: 200px 100%;
  animation: shimmer 1.4s ease infinite;
  border-radius: 4px;
}

/* Card hover effect */
.el-card {
  transition: box-shadow 0.3s ease, transform 0.2s ease;
}
.el-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Responsive table */
@media (max-width: 768px) {
  .el-table .cell {
    white-space: normal !important;
  }
  .el-card__header {
    flex-wrap: wrap !important;
  }
}

/* Global scroll bar */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-thumb {
  background: #c0c4cc;
  border-radius: 3px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
</style>