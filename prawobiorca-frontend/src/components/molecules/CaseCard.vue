<script setup lang="ts">
import { ref } from 'vue'
import { deleteUserCase } from '@/api/generated/endpoints/cases/cases'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import DeleteOutlineRoundedIcon from '@iconify-vue/material-symbols/delete-outline-rounded'
import ArrowRightAltRoundedIcon from '@iconify-vue/material-symbols/arrow-right-alt-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'

type Props = {
  userCase: {
    id: string
    name: string
  }
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
    showApiError(error, { defaultServerMessage: 'Nie udało się usunąć sprawy' })
  } finally {
    isDeleting.value = false
  }
}
</script>

<template>
  <router-link :to="`/user/cases/${userCase.id}`" class="case-card-link">
    <el-card shadow="hover" class="case-card">
      <div class="card-content">
        <div class="case-info">
          <span class="case-name" :title="userCase.name">{{ userCase.name }}</span>
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
              <button class="icon-btn icon-btn-danger" :disabled="isDeleting" @click.prevent.stop>
                <DeleteOutlineRoundedIcon />
              </button>
            </template>
          </el-popconfirm>
        </div>
      </div>
    </el-card>
  </router-link>
</template>

<style scoped>
.case-card {
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

.icon-btn-danger:hover {
  color: var(--el-color-danger);
}

.icon-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.case-card-link {
  display: block;
  color: inherit;
  text-decoration: none;
}
</style>
