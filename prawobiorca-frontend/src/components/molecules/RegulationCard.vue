<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  confirmPublicRegulationUpload,
  retryPublicRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  confirmUserRegulationUpload,
  retryUserRegulationPreparation,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import DescriptionOutlineRoundedIcon from '@iconify-vue/material-symbols/description-outline-rounded'
import SearchRoundedIcon from '@iconify-vue/material-symbols/search-rounded'
import MoreVertIcon from '@iconify-vue/material-symbols/more-vert'
import RefreshRoundedIcon from '@iconify-vue/material-symbols/refresh-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'
import RegulationTypeBadge from '@/components/atoms/RegulationTypeBadge.vue'
import RegulationStatusBadge from '@/components/atoms/RegulationStatusBadge.vue'
import RegulationDetailsDialog from '@/components/molecules/RegulationDetailsDialog.vue'
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
  (e: 'updated', regulation: RegulationRepresentation): void
  (e: 'deleted', regulationId: string): void
  (e: 'preparation-retried', regulationId: string): void
}>()

const isDetailsDialogVisible = ref(false)
const isPrepared = computed(() => props.regulation.preparationStatus === 'PREPARED')
const isNotStarted = computed(() => props.regulation.preparationStatus === 'NOT_STARTED')
const canRetry = computed(
  () => isNotStarted.value || props.regulation.preparationStatus === 'FAILED',
)

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

async function retryPreparation(regulationId: string) {
  const { retry } = isNotStarted.value ? uploadConfirmation : preparationRetry
  if (await retry(regulationId)) {
    emit('preparation-retried', regulationId)
  }
}
</script>

<template>
  <div class="regulation-item" :class="{ 'is-prepared': isPrepared }">
    <DescriptionOutlineRoundedIcon class="regulation-icon" />

    <component
      :is="isPrepared ? 'router-link' : 'span'"
      :to="
        isPrepared ? { name: searchRouteName, params: { regulationId: regulation.id } } : undefined
      "
      class="regulation-name app-text-truncate"
      :class="{ 'regulation-link': isPrepared }"
      :title="regulation.presentationName"
    >
      {{ regulation.presentationName }}
    </component>

    <div class="app-card-actions">
      <RegulationTypeBadge :regulation-type="regulation.regulationType" />

      <template v-if="!isPrepared && canManage">
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

      <span v-if="isPrepared">
        <IconMotion motion-type="search" class="search-action">
          <SearchRoundedIcon />
        </IconMotion>
      </span>

      <button
        type="button"
        class="icon-btn options-btn"
        aria-label="Opcje regulacji"
        @click="isDetailsDialogVisible = true"
      >
        <MoreVertIcon />
      </button>
    </div>

    <RegulationDetailsDialog
      v-model="isDetailsDialogVisible"
      :regulation="regulation"
      :target="target"
      :can-manage="canManage"
      @updated="(updatedRegulation) => emit('updated', updatedRegulation)"
      @deleted="(regulationId) => emit('deleted', regulationId)"
    />
  </div>
</template>

<style scoped>
.regulation-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  padding: var(--app-space-sm) var(--app-space-lg);
  transition: background-color 0.2s ease;
}

.regulation-item + .regulation-item {
  border-top: 1px solid var(--app-card-border);
}

.regulation-item.is-prepared:hover {
  background-color: var(--el-color-primary-light-9);
}

.regulation-icon {
  flex-shrink: 0;
  width: 1.5em;
  height: 1.5em;
  color: var(--el-color-primary);
}

.regulation-name {
  flex: 1;
  min-width: 0;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.regulation-link {
  text-decoration: none;
}

.regulation-link::after {
  content: '';
  position: absolute;
  inset: 0;
}

.regulation-item.is-prepared:hover .regulation-name,
.regulation-item.is-prepared:hover .search-action {
  color: var(--el-color-primary);
}

.options-btn:hover {
  color: var(--el-color-primary);
}

.app-card-actions button {
  position: relative;
  z-index: 1;
}
</style>
