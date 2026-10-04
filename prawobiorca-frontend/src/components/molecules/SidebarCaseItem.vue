<script setup lang="ts">
import { ref } from 'vue'
import { deleteUserCase } from '@/api/generated/endpoints/cases/cases'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import DeleteOutlineRoundedIcon from '@iconify-vue/material-symbols/delete-outline-rounded'
import KeepRoundedIcon from '@iconify-vue/material-symbols/keep-rounded'
import KeepOutlineRoundedIcon from '@iconify-vue/material-symbols/keep-outline-rounded'
import type { CaseData } from '@/api/generated/model'

type Props = {
  userCase: CaseData
  isActive: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'deleted', caseId: string): void
  (e: 'activate', caseId: string): void
}>()

const isDeleting = ref(false)

async function handleDelete() {
  try {
    isDeleting.value = true
    await deleteUserCase(props.userCase.id)
    ElMessage.success('Sprawa została usunięta')
    emit('deleted', props.userCase.id)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć sprawy' })
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <div class="sidebar-case-item">
    <router-link
      :to="{ name: 'CasePage', params: { id: userCase.id } }"
      class="case-name"
      active-class="is-active"
      :title="userCase.name"
    >
      {{ userCase.name }}
    </router-link>
    <button
      type="button"
      :class="['icon-btn', 'icon-btn-pin', { 'is-active': isActive }]"
      aria-label="Ustaw jako aktywną sprawę"
      title="Ustaw jako aktywną sprawę"
      @click="emit('activate', userCase.id)"
    >
      <KeepRoundedIcon v-if="isActive" />
      <KeepOutlineRoundedIcon v-else />
    </button>
    <el-popconfirm
      title="Czy na pewno chcesz usunąć tę sprawę?"
      confirm-button-text="Tak"
      cancel-button-text="Nie"
      @confirm="handleDelete"
    >
      <template #reference>
        <button
          type="button"
          class="icon-btn icon-btn-danger"
          aria-label="Usuń sprawę"
          :disabled="isDeleting"
        >
          <DeleteOutlineRoundedIcon />
        </button>
      </template>
    </el-popconfirm>
  </div>
</template>

<style scoped>
.sidebar-case-item {
  display: flex;
  align-items: center;
  border-radius: 4px;

  &:hover {
    background-color: var(--el-menu-hover-bg-color);
  }

  &:not(:hover) .icon-btn:not(.is-active) {
    visibility: hidden;
  }
}

.icon-btn-pin.is-active {
  color: var(--el-color-primary);
}

.case-name {
  flex: 1;
  min-width: 0;
  height: var(--el-menu-item-height);
  line-height: var(--el-menu-item-height);
  padding-left: var(--el-menu-base-level-padding);
  font-size: var(--el-menu-item-font-size);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  color: var(--el-text-color-primary);
  text-decoration: none;

  &.is-active {
    color: var(--el-menu-active-color);
  }
}

.icon-btn-danger:hover {
  color: var(--el-color-danger);
}
</style>
