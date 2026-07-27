<template>
  <v-chart :option="option" autoresize style="height: 300px" />
</template>

<script setup lang="ts">
defineProps<{
  option: any
}>()
</script>