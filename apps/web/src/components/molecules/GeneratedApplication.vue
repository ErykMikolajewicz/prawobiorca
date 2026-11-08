<script setup lang="ts">
import { computed } from 'vue'
import ApplicationStatusBadge from '@/components/atoms/ApplicationStatusBadge.vue'
import type { ApplicationRepresentation } from '@/api/generated/model'

type Props = { application: ApplicationRepresentation }
const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'download', id: string): void
  (e: 'delete', id: string): void
}>()

const name = computed(() => props.application.name ?? props.application.templateName)
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
  <el-card shadow="never" class="generated-application app-card">
    <div class="app-card-content">
      <strong class="name">{{ name }}</strong>
      <div class="app-card-actions">
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
    <div class="meta">Szablon: {{ application.templateName }} · {{ createDate }}</div>
  </el-card>
</template>

<style scoped>
.generated-application :deep(.el-card__body) {
  padding-bottom: var(--app-space-sm);
}

.name {
  flex: 1;
  min-width: 0;
  font-size: 1.15rem;
  overflow-wrap: anywhere;
}

.meta {
  margin-top: var(--app-space-lg);
  text-align: right;
  font-size: 0.75rem;
  color: var(--el-text-color-secondary);
}

@media (width <= 768px) {
  .app-card-content {
    flex-wrap: wrap;
  }

  .name {
    flex-basis: 100%;
  }
}
</style>
