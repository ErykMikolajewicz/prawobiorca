<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  deleteUserRegulation,
  retryUserRegulationPreparation,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '@/utils/error'
import SearchRoundedIcon from '@iconify-vue/material-symbols/search-rounded'
import DeleteOutlineRoundedIcon from '@iconify-vue/material-symbols/delete-outline-rounded'
import RefreshRoundedIcon from '@iconify-vue/material-symbols/refresh-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'
import RegulationTypeBadge from '@/components/atoms/RegulationTypeBadge.vue'
import RegulationStatusBadge from '@/components/atoms/RegulationStatusBadge.vue'
import { useRegulationPreparation } from '@/composables/useRegulationPreparation'
import type { RegulationRepresentation } from '@/api/generated/model'

type Props = {
  regulation: RegulationRepresentation
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'deleted', regulationId: string): void
  (e: 'preparation-retried', regulationId: string): void
}>()

const isDeleting = ref(false)
const isPrepared = computed(() => props.regulation.preparationStatus === 'PREPARED')
const hasFailed = computed(() => props.regulation.preparationStatus === 'FAILED')

const { isRetrying, retry } = useRegulationPreparation(retryUserRegulationPreparation)

async function handleDelete() {
  try {
    isDeleting.value = true
    await deleteUserRegulation(props.regulation.id)
    ElMessage.success('Regulacja została usunięta')
    emit('deleted', props.regulation.id)
  } catch (error) {
    ElMessage.error(
      getApiErrorMessage(error, { defaultServerMessage: 'Nie udało się usunąć regulacji' }),
    )
    console.error(error)
  } finally {
    isDeleting.value = false
  }
}

async function retryPreparation(regulationId: string) {
  if (await retry(regulationId)) {
    emit('preparation-retried', regulationId)
  }
}
</script>

<template>
  <component
    :is="isPrepared ? 'router-link' : 'div'"
    :to="
      isPrepared
        ? {
            name: 'SearchUserRegulation',
            params: { regulationId: regulation.id },
            state: { filename: regulation.presentationName },
          }
        : undefined
    "
    :class="isPrepared ? 'file-card-link' : ''"
  >
    <el-card shadow="hover" class="file-card">
      <RegulationTypeBadge :regulation-type="regulation.regulationType" class="type-badge" />
      <div class="card-content">
        <div class="regulation-info">
          <span class="regulation-name" :title="regulation.presentationName">{{
            regulation.presentationName
          }}</span>
        </div>

        <div class="actions">
          <span v-if="isPrepared">
            <IconMotion motion-type="search">
              <SearchRoundedIcon />
            </IconMotion>
          </span>

          <template v-else>
            <RegulationStatusBadge :preparation-status="regulation.preparationStatus" />

            <form
              v-if="hasFailed"
              class="form-action"
              @submit.prevent="retryPreparation(regulation.id)"
            >
              <button class="icon-btn" type="submit" :disabled="isRetrying">
                <RefreshRoundedIcon />
              </button>
            </form>
          </template>

          <el-popconfirm
            title="Czy na pewno chcesz usunąć tę regulację?"
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
  </component>
</template>

<style scoped>
.file-card {
  position: relative;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
  height: 100%;
}

.file-card:hover {
  box-shadow: var(--app-card-shadow);
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 18px;
}

.regulation-info {
  flex: 1;
  min-width: 0;
}

.regulation-name {
  display: block;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.type-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 1;
}

.file-card-link {
  display: block;
  color: inherit;
  text-decoration: none;
}

.file-card-link:hover {
  .file-card {
    box-shadow: var(--app-card-shadow);
  }

  :deep(.icon-btn) {
    color: var(--el-color-primary);
  }
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
  align-items: center;
}

.form-action {
  margin: 0;
  padding: 0;
  border: none;
  background: none;
}
</style>
