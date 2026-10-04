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
const createDate = computed(() =>
  new Date(props.application.createDate).toLocaleString('pl-PL', {
    dateStyle: 'short',
    timeStyle: 'short',
  }),
)
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
    <div class="card-content">
      <div class="application-info">
        <strong>{{ label }}</strong>
        <em>{{ createDate }}</em>
      </div>
      <div class="actions">
        <el-button v-if="isGenerated" type="primary" @click="handleDownload">Pobierz</el-button>
        <ApplicationStatusBadge v-else :generation-status="application.generationStatus" />
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
      </div>
    </div>
  </el-card>
</template>

<style scoped>
.card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.application-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}
</style>
