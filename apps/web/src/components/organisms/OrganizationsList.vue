<script setup lang="ts">
import type { OrganizationData, SuborganizationData } from '@/api/generated/model'

type Props = {
  organizations: Array<OrganizationData>
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'edit-organization', organization: OrganizationData): void
  (e: 'delete-organization', organizationId: string): void
  (e: 'add-suborganization', organizationId: string): void
  (e: 'edit-suborganization', organizationId: string, suborganization: SuborganizationData): void
  (e: 'delete-suborganization', organizationId: string, suborganizationId: string): void
}>()
</script>

<template>
  <el-collapse v-if="organizations.length" class="app-collapse organizations-collapse">
    <el-collapse-item
      v-for="organization in organizations"
      :key="organization.id"
      :name="organization.id"
    >
      <template #title>
        <span class="organization-header">
          <span class="item-name app-text-truncate" :title="organization.name">
            {{ organization.name }}
            <span class="organization-short-name">({{ organization.shortName }})</span>
          </span>
          <span class="app-actions" @click.stop @keydown.stop>
            <el-button size="small" @click="emit('add-suborganization', organization.id)">
              Dodaj podorganizację
            </el-button>
            <el-button size="small" @click="emit('edit-organization', organization)">
              Edytuj
            </el-button>
            <el-popconfirm
              title="Czy na pewno chcesz usunąć tę organizację wraz z podorganizacjami?"
              confirm-button-text="Tak"
              cancel-button-text="Nie"
              :width="260"
              @confirm="emit('delete-organization', organization.id)"
            >
              <template #reference>
                <el-button type="danger" plain size="small">Usuń</el-button>
              </template>
            </el-popconfirm>
          </span>
        </span>
      </template>

      <ul v-if="organization.suborganizations.length" class="suborganizations-list app-list-reset">
        <li
          v-for="suborganization in organization.suborganizations"
          :key="suborganization.id"
          class="suborganization-item"
        >
          <span class="item-name app-text-truncate" :title="suborganization.name">{{
            suborganization.name
          }}</span>
          <span class="app-actions">
            <el-button
              size="small"
              @click="emit('edit-suborganization', organization.id, suborganization)"
            >
              Edytuj
            </el-button>
            <el-popconfirm
              title="Czy na pewno chcesz usunąć tę podorganizację?"
              confirm-button-text="Tak"
              cancel-button-text="Nie"
              @confirm="emit('delete-suborganization', organization.id, suborganization.id)"
            >
              <template #reference>
                <el-button type="danger" plain size="small">Usuń</el-button>
              </template>
            </el-popconfirm>
          </span>
        </li>
      </ul>
      <p v-else class="suborganizations-empty">Brak podorganizacji.</p>
    </el-collapse-item>
  </el-collapse>

  <el-empty v-else description="Brak organizacji." />
</template>

<style scoped>
.organizations-collapse :deep(.el-collapse-item__header) {
  border-left: 4px solid var(--el-color-primary);
}

.organizations-collapse :deep(.el-collapse-item__title) {
  flex: 1;
  min-width: 0;
}

.organization-header {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  padding-right: var(--app-space-md);
}

.item-name {
  flex: 1;
  min-width: 0;
  font-weight: 500;
}

.organization-short-name {
  color: var(--el-text-color-secondary);
  font-weight: normal;
}

.suborganizations-list {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.suborganization-item {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  padding: var(--app-space-sm) var(--app-space-md) var(--app-space-sm) var(--app-space-xl);
  border-radius: var(--app-radius-lg);
  border: 1px solid var(--el-border-color-lighter);
  border-left: 3px solid var(--el-color-primary-light-5);
  transition: border-color 0.2s ease;
}

.suborganization-item:hover {
  border-color: var(--el-color-primary-light-5);
}

.suborganization-item .item-name {
  font-weight: normal;
}

.suborganizations-empty {
  margin: 0;
  padding-left: var(--app-space-xl);
  color: var(--el-text-color-secondary);
}

@media (width <= 768px) {
  .organizations-collapse :deep(.el-collapse-item__header) {
    line-height: normal;
  }

  .organization-header {
    flex-wrap: wrap;
    padding-block: var(--app-space-sm);
  }

  .organization-header .item-name,
  .suborganization-item .item-name {
    flex-basis: 100%;
  }

  .suborganization-item {
    flex-wrap: wrap;
  }
}
</style>
