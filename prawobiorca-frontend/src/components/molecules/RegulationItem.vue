<script setup lang="ts">
import { computed } from 'vue'
import DescriptionOutlineRoundedIcon from '@iconify-vue/material-symbols/description-outline-rounded'
import SearchRoundedIcon from '@iconify-vue/material-symbols/search-rounded'
import MoreVertIcon from '@iconify-vue/material-symbols/more-vert'
import RefreshRoundedIcon from '@iconify-vue/material-symbols/refresh-rounded'
import IconMotion from '@/components/atoms/IconMotion.vue'
import RegulationTypeBadge from '@/components/atoms/RegulationTypeBadge.vue'
import RegulationStatusBadge from '@/components/atoms/RegulationStatusBadge.vue'
import { useRegulationPreparation } from '@/composables/useRegulationPreparation'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationRepresentation } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

type Props = {
  regulation: RegulationRepresentation
  target: RegulationScope
  canManage: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'open-details', regulationId: string): void
  (e: 'preparation-retried', regulationId: string): void
}>()

const organizationsStore = useOrganizationsStore()
const { isRetrying, retry } = useRegulationPreparation(props.target)

const organizationLabel = computed(() => {
  const organization = organizationsStore.organizations.find(
    (o) => o.id === props.regulation.organizationId,
  )
  if (!organization) {
    return null
  }
  const suborganization = organization.suborganizations.find(
    (s) => s.id === props.regulation.suborganizationId,
  )
  return suborganization
    ? `${organization.shortName} · ${suborganization.name}`
    : organization.shortName
})
const isPrepared = computed(() => props.regulation.preparationStatus === 'PREPARED')
const canRetry = computed(
  () =>
    props.regulation.preparationStatus === 'NOT_STARTED' ||
    props.regulation.preparationStatus === 'FAILED',
)

const searchRouteName =
  props.target === 'public' ? 'SearchPublicRegulation' : 'SearchUserRegulation'

async function retryPreparation() {
  if (await retry(props.regulation)) {
    emit('preparation-retried', props.regulation.id)
  }
}
</script>

<template>
  <div class="regulation-item" :class="{ 'is-prepared': isPrepared }">
    <DescriptionOutlineRoundedIcon class="regulation-icon" />

    <div class="regulation-content">
      <component
        :is="isPrepared ? 'router-link' : 'span'"
        :to="
          isPrepared
            ? { name: searchRouteName, params: { regulationId: regulation.id } }
            : undefined
        "
        class="regulation-name app-text-truncate"
        :class="{ 'regulation-link': isPrepared }"
        :title="regulation.presentationName"
      >
        {{ regulation.presentationName }}
      </component>

      <div class="regulation-meta">
        <span
          v-if="organizationLabel"
          class="regulation-organization app-text-secondary app-text-truncate"
          :title="organizationLabel"
        >
          {{ organizationLabel }}
        </span>

        <RegulationTypeBadge :regulation-type="regulation.regulationType" />

        <RegulationStatusBadge
          v-if="!isPrepared && canManage"
          :preparation-status="regulation.preparationStatus"
        />
      </div>
    </div>

    <div class="app-card-actions">
      <button
        v-if="canManage && canRetry"
        class="icon-btn"
        type="button"
        aria-label="Ponów przetwarzanie"
        :disabled="isRetrying"
        @click="retryPreparation"
      >
        <RefreshRoundedIcon />
      </button>

      <span v-if="isPrepared">
        <IconMotion motion-type="search" class="search-action">
          <SearchRoundedIcon />
        </IconMotion>
      </span>

      <button
        type="button"
        class="icon-btn is-primary"
        aria-label="Opcje regulacji"
        @click="emit('open-details', regulation.id)"
      >
        <MoreVertIcon />
      </button>
    </div>
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

.regulation-content {
  display: flex;
  flex: 1;
  align-items: center;
  gap: var(--app-space-md);
  min-width: 0;
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

.regulation-meta {
  display: flex;
  flex-shrink: 0;
  align-items: center;
  gap: var(--app-space-sm);
}

.regulation-organization {
  max-width: 16em;
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

.app-card-actions button {
  position: relative;
  z-index: 1;
}

@media (width <= 768px) {
  .regulation-item {
    gap: var(--app-space-sm);
    padding: var(--app-space-sm) var(--app-space-xs) var(--app-space-sm) var(--app-space-md);
  }

  .regulation-content {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--app-space-xs);
  }

  .regulation-name {
    flex: none;
    max-width: 100%;
    white-space: normal;
  }

  .regulation-meta {
    flex-wrap: wrap;
    max-width: 100%;
  }

  .regulation-organization {
    min-width: 0;
  }

  .app-card-actions {
    gap: 0;
  }
}
</style>
