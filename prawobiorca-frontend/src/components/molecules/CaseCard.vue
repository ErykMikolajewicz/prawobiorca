<script setup lang="ts">
import { ref } from 'vue'
import { deleteUserCase } from '@/api/generated/endpoints/cases/cases'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import DeleteOutlineRoundedIcon from '@iconify-vue/material-symbols/delete-outline-rounded'
import ArrowRightAltRoundedIcon from '@iconify-vue/material-symbols/arrow-right-alt-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'
import type { CaseData } from '@/api/generated/model'

type Props = {
  userCase: CaseData
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'deleted', caseId: string): void
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
  <el-card shadow="never" class="case-card app-card">
    <div class="card-content">
      <div class="case-info">
        <router-link
          :to="{ name: 'CasePage', params: { id: userCase.id } }"
          class="case-name case-card-link"
          :title="userCase.name"
        >
          {{ userCase.name }}
        </router-link>
      </div>
      <div class="actions">
        <IconMotion motion-type="arrow">
          <ArrowRightAltRoundedIcon />
        </IconMotion>
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
    </div>
  </el-card>
</template>

<style scoped>
.case-card {
  position: relative;
  height: 100%;
}

.card-content {
  margin-inline: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.case-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.case-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.actions button {
  position: relative;
  z-index: 1;
}

.case-card-link {
  text-decoration: none;
}

.case-card-link::after {
  content: '';
  position: absolute;
  inset: 0;
}

.icon-btn-danger:hover {
  color: var(--el-color-danger);
}
</style>
