<script setup lang="ts">
import { computed } from 'vue'
import ApplicationStatusBadge from '@/components/atoms/ApplicationStatusBadge.vue'
import { applicationTypeOptions } from '@/domain/applications'
import type { ApplicationRepresentation } from '@/api/generated/model'

type Props = { application: ApplicationRepresentation }
const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'download', id: string): void
  (e: 'delete', id: string): void
}>()

const label = computed(
  () =>
    applicationTypeOptions.find((option) => option.value === props.application.applicationType)
      ?.label,
)
const createDate = computed(() => new Date(props.application.createDate).toLocaleString('pl-PL'))
const isGenerated = computed(() => props.application.generationStatus === 'GENERATED')

function handleDownload() {
  emit('download', props.application.id)
}

function handleDelete() {
  emit('delete', props.application.id)
}
</script>

<template>
  <el-card shadow="hover">
    <template #header>
      <strong>{{ label }}</strong>
      <em>{{ createDate }}</em>
      <ApplicationStatusBadge :generation-status="application.generationStatus" />
      <el-button type="primary" :disabled="!isGenerated" @click="handleDownload">Pobierz</el-button>
      <el-popconfirm
        title="Czy na pewno chcesz usunąć ten wniosek?"
        confirm-button-text="Tak"
        cancel-button-text="Nie"
        @confirm="handleDelete"
      >
        <template #reference>
          <el-button type="danger">Usuń</el-button>
        </template>
      </el-popconfirm>
    </template>
  </el-card>
</template>
