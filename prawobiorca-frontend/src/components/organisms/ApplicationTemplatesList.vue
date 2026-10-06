<script setup lang="ts">
import ApplicationTemplateStatusBadge from '@/components/atoms/ApplicationTemplateStatusBadge.vue'
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
</script>

<template>
  <div v-loading="loading" class="templates-list">
    <template v-if="templates.length">
      <div
        v-for="template in templates"
        :key="template.id"
        class="template-item app-card"
        @click="emit('select', template.id)"
      >
        <span class="template-name" :title="template.name">{{ template.name }}</span>
        <ApplicationTemplateStatusBadge :status="template.status" />
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
  </div>
</template>

<style scoped>
.templates-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-height: 80px;
}

.template-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.template-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
</style>
