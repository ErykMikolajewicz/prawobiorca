<script setup lang="ts">
import { ref } from 'vue'
import ApplicationTemplateStatusBadge from '@/components/atoms/ApplicationTemplateStatusBadge.vue'
import ApplicationTemplatePreviewDialog from '@/components/molecules/ApplicationTemplatePreviewDialog.vue'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

type Props = {
  templates: Array<ApplicationTemplateRepresentation>
  loading?: boolean
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'select', templateId: string): void
  (e: 'delete', templateId: string): void
}>()

const previewTemplateId = ref('')
const isPreviewVisible = ref(false)

function showPreview(templateId: string) {
  previewTemplateId.value = templateId
  isPreviewVisible.value = true
}
</script>

<template>
  <div v-loading="loading" class="templates-list">
    <template v-if="templates.length">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-item app-card is-interactive"
        @click="emit('select', template.id)"
      >
        <span class="template-name app-text-truncate" :title="template.name">{{
          template.name
        }}</span>
        <ApplicationTemplateStatusBadge :status="template.status" />
        <el-button
          v-if="template.status !== 'NOT_UPLOADED'"
          size="small"
          @click.stop="showPreview(template.id)"
        >
          Pokaż podgląd
        </el-button>
        <el-popconfirm
          title="Czy na pewno chcesz usunąć ten szablon?"
          confirm-button-text="Tak"
          cancel-button-text="Nie"
          @confirm="emit('delete', template.id)"
        >
          <template #reference>
            <el-button type="danger" plain size="small" @click.stop>Usuń</el-button>
          </template>
        </el-popconfirm>
      </div>
    </template>

    <el-empty v-else-if="!loading" description="Brak szablonów wniosków." />

    <ApplicationTemplatePreviewDialog v-model="isPreviewVisible" :template-id="previewTemplateId" />
  </div>
</template>

<style scoped>
.templates-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  min-height: 80px;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--app-space-md);
  padding: var(--app-space-lg);
  border: 1px solid var(--app-card-border);
  border-radius: var(--app-radius-lg);
  background: var(--app-card-bg);
  color: var(--el-text-color-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.template-name {
  flex: 1;
  min-width: 0;
  font-weight: 500;
}

@media (width <= 768px) {
  .template-item {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .template-name {
    flex-basis: 100%;
  }
}
</style>
