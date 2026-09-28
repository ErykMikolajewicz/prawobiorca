<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  confirmPublicRegulationUpload,
  deletePublicRegulation,
  retryPublicRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  confirmUserRegulationUpload,
  deleteUserRegulation,
  retryUserRegulationPreparation,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import SearchRoundedIcon from '@iconify-vue/material-symbols/search-rounded'
import DeleteOutlineRoundedIcon from '@iconify-vue/material-symbols/delete-outline-rounded'
import RefreshRoundedIcon from '@iconify-vue/material-symbols/refresh-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'
import RegulationTypeBadge from '@/components/atoms/RegulationTypeBadge.vue'
import RegulationStatusBadge from '@/components/atoms/RegulationStatusBadge.vue'
import { useRegulationPreparation } from '@/composables/useRegulationPreparation'
import type { RegulationRepresentation } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

type Props = {
  regulation: RegulationRepresentation
  target: RegulationScope
  canManage: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'deleted', regulationId: string): void
  (e: 'preparation-retried', regulationId: string): void
}>()

const isDeleting = ref(false)
const isPrepared = computed(() => props.regulation.preparationStatus === 'PREPARED')
const isNotStarted = computed(() => props.regulation.preparationStatus === 'NOT_STARTED')
const canRetry = computed(
  () => isNotStarted.value || props.regulation.preparationStatus === 'FAILED',
)

const deleteRegulation = props.target === 'public' ? deletePublicRegulation : deleteUserRegulation
const retryRegulationPreparation =
  props.target === 'public' ? retryPublicRegulationPreparation : retryUserRegulationPreparation
const confirmRegulationUpload =
  props.target === 'public' ? confirmPublicRegulationUpload : confirmUserRegulationUpload
const searchRouteName =
  props.target === 'public' ? 'SearchPublicRegulation' : 'SearchUserRegulation'

const preparationRetry = useRegulationPreparation(retryRegulationPreparation)
const uploadConfirmation = useRegulationPreparation(
  confirmRegulationUpload,
  'Pliku nie ma w magazynie. Usuń regulację i dodaj ją ponownie.',
)
const isRetrying = computed(
  () => preparationRetry.isRetrying.value || uploadConfirmation.isRetrying.value,
)

async function handleDelete() {
  try {
    isDeleting.value = true
    await deleteRegulation(props.regulation.id)
    ElMessage.success('Regulacja została usunięta')
    emit('deleted', props.regulation.id)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć regulacji' })
  } finally {
    isDeleting.value = false
  }
}

async function retryPreparation(regulationId: string) {
  const { retry } = isNotStarted.value ? uploadConfirmation : preparationRetry
  if (await retry(regulationId)) {
    emit('preparation-retried', regulationId)
  }
}
</script>

<template>
  <el-card shadow="hover" class="file-card" :class="{ 'file-card--prepared': isPrepared }">
    <RegulationTypeBadge :regulation-type="regulation.regulationType" class="type-badge" />
    <div class="card-content">
      <div class="regulation-info">
        <component
          :is="isPrepared ? 'router-link' : 'span'"
          :to="
            isPrepared
              ? { name: searchRouteName, params: { regulationId: regulation.id } }
              : undefined
          "
          class="regulation-name"
          :class="{ 'file-card-link': isPrepared }"
          :title="regulation.presentationName"
        >
          {{ regulation.presentationName }}
        </component>
      </div>

      <div class="actions">
        <span v-if="isPrepared">
          <IconMotion motion-type="search" class="search-action">
            <SearchRoundedIcon />
          </IconMotion>
        </span>

        <template v-else-if="canManage">
          <RegulationStatusBadge :preparation-status="regulation.preparationStatus" />

          <button
            v-if="canRetry"
            class="icon-btn"
            type="button"
            aria-label="Ponów przetwarzanie"
            :disabled="isRetrying"
            @click="retryPreparation(regulation.id)"
          >
            <RefreshRoundedIcon />
          </button>
        </template>

        <el-popconfirm
          v-if="canManage"
          title="Czy na pewno chcesz usunąć tę regulację?"
          confirm-button-text="Tak"
          cancel-button-text="Nie"
          @confirm="handleDelete"
        >
          <template #reference>
            <button
              type="button"
              class="icon-btn icon-btn-danger"
              aria-label="Usuń regulację"
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
  text-decoration: none;
}

.file-card-link::after {
  content: '';
  position: absolute;
  inset: 0;
}

.file-card--prepared:hover .search-action {
  color: var(--el-color-primary);
}

.actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  align-items: center;
}

.actions button {
  position: relative;
  z-index: 1;
}
</style>
