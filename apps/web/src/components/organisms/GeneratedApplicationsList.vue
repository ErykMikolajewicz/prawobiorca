<script setup lang="ts">
import GeneratedApplication from '@/components/molecules/GeneratedApplication.vue'
import type { ApplicationRepresentation } from '@/api/generated/model'

defineProps<{ applications: Array<ApplicationRepresentation> }>()

const emit = defineEmits<{
  (e: 'download', id: string): void
  (e: 'delete', id: string): void
}>()

function handleDownload(id: string) {
  emit('download', id)
}

function handleDelete(id: string) {
  emit('delete', id)
}
</script>

<template>
  <div v-if="applications.length > 0">
    <GeneratedApplication
      v-for="application in applications"
      :key="application.id"
      :application="application"
      @download="handleDownload"
      @delete="handleDelete"
    />
  </div>
  <div v-else>
    <el-empty description="Brak wygenerowanych wniosków do tej sprawy." />
  </div>
</template>
