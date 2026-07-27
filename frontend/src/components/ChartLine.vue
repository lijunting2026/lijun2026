<template>
  <v-chart :option="option" autoresize style="height: 320px" />
</template>

<script setup lang="ts">
defineProps<{
  option: any
}>()
</script>