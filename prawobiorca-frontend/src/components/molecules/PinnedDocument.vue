<script setup lang="ts">
import type { CaseDocument } from '@/api/generated/model'

type Props = { document: CaseDocument }
const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'unpin', id: string): void
}>()

const handleUnpin = () => {
  emit('unpin', props.document.id)
}
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <strong>Źródło:</strong>
      <em>{{ document.presentationName }}</em>
      <el-button type="danger" @click="handleUnpin">Odepnij</el-button>
    </template>
    <p>{{ document.content }}</p>
  </el-card>
</template>
