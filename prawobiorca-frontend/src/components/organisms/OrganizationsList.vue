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
  (e: 'edit-suborganization', suborganization: SuborganizationData): void
  (e: 'delete-suborganization', suborganizationId: string): void
}>()
</script>

<template>
  <el-collapse v-if="organizations.length" class="organizations-collapse">
    <el-collapse-item
      v-for="organization in organizations"
      :key="organization.id"
      :name="organization.id"
    >
      <template #title>
        <span class="organization-header">
          <span class="item-name" :title="organization.name">
            {{ organization.name }}
            <span class="organization-short-name">({{ organization.shortName }})</span>
          </span>
          <span class="item-actions" @click.stop @keydown.stop>
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

      <ul v-if="organization.suborganizations.length" class="suborganizations-list">
        <li
          v-for="suborganization in organization.suborganizations"
          :key="suborganization.id"
          class="suborganization-item"
        >
          <span class="item-name" :title="suborganization.name">{{ suborganization.name }}</span>
          <span class="item-actions">
            <el-button size="small" @click="emit('edit-suborganization', suborganization)">
              Edytuj
            </el-button>
            <el-popconfirm
              title="Czy na pewno chcesz usunąć tę podorganizację?"
              confirm-button-text="Tak"
              cancel-button-text="Nie"
              @confirm="emit('delete-suborganization', suborganization.id)"
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
.organizations-collapse {
  --el-collapse-header-bg-color: transparent;
  --el-collapse-content-bg-color: transparent;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.organizations-collapse :deep(.el-collapse-item__header),
.organizations-collapse :deep(.el-collapse-item__content) {
  padding-left: 16px;
  padding-right: 16px;
}

.organizations-collapse :deep(.el-collapse-item__title) {
  flex: 1;
  min-width: 0;
}

.organization-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-right: 12px;
}

.item-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

.organization-short-name {
  color: var(--el-text-color-secondary);
  font-weight: normal;
}

.item-actions {
  display: flex;
  align-items: center;
  gap: 8px;

  .el-button + .el-button {
    margin-left: 0;
  }
}

.suborganizations-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.suborganization-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px 8px 24px;
  border-radius: 6px;
  background-color: var(--el-fill-color-lighter);

  .item-name {
    font-weight: normal;
  }
}

.suborganizations-empty {
  margin: 0;
  padding-left: 24px;
  color: var(--el-text-color-secondary);
}
</style>
