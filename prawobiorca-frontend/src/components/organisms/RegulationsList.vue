<script setup lang="ts">
import { computed, ref } from 'vue'
import RegulationItem from '@/components/molecules/RegulationItem.vue'
import RegulationDetailsDialog from '@/components/molecules/RegulationDetailsDialog.vue'
import RegulationTypeFilter from '@/components/molecules/RegulationTypeFilter.vue'
import RegulationOrganizationFilter from '@/components/molecules/RegulationOrganizationFilter.vue'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

type Props = {
  title: string
  emptyDescription: string
  regulations: Array<RegulationRepresentation>
  target: RegulationScope
  canManage: boolean
  loading?: boolean
  scores?: Record<string, number>
}

const props = defineProps<Props>()

const typeFilter = defineModel<RegulationType | undefined>('typeFilter')

const emit = defineEmits<{
  (e: 'regulation-updated', regulation: RegulationRepresentation): void
  (e: 'regulation-deleted', regulationId: string): void
  (e: 'regulation-preparation-retried', regulationId: string): void
  (e: 'regulation-description-generation-started', regulationId: string): void
}>()

const isDetailsDialogVisible = ref(false)
const selectedRegulationId = ref<string>()

const selectedRegulation = computed(() =>
  props.regulations.find((regulation) => regulation.id === selectedRegulationId.value),
)

const displayedRegulations = computed(() => {
  if (props.canManage) {
    return props.regulations
  }
  return props.regulations.filter((regulation) => regulation.preparationStatus === 'PREPARED')
})

function openDetails(regulationId: string) {
  selectedRegulationId.value = regulationId
  isDetailsDialogVisible.value = true
}
</script>

<template>
  <div v-loading="loading" class="regulations-container">
    <div class="list-header">
      <h2 class="section-title">{{ title }}</h2>
      <slot name="actions" />
    </div>

    <div class="filter-row">
      <RegulationTypeFilter v-model="typeFilter" />
      <RegulationOrganizationFilter v-if="target === 'PUBLIC'" />
    </div>

    <div v-if="displayedRegulations.length" class="regulations-list">
      <RegulationItem
        v-for="regulation in displayedRegulations"
        :key="regulation.id"
        :regulation="regulation"
        :target="target"
        :can-manage="canManage"
        :score="scores?.[regulation.id]"
        @open-details="openDetails"
        @preparation-retried="
          (regulationId) => emit('regulation-preparation-retried', regulationId)
        "
      />
    </div>

    <el-empty v-else-if="!loading" :description="emptyDescription" />

    <RegulationDetailsDialog
      v-if="selectedRegulation"
      v-model="isDetailsDialogVisible"
      :regulation="selectedRegulation"
      :can-manage="canManage"
      @updated="(updatedRegulation) => emit('regulation-updated', updatedRegulation)"
      @deleted="(regulationId) => emit('regulation-deleted', regulationId)"
      @description-generation-started="
        (regulationId) => emit('regulation-description-generation-started', regulationId)
      "
    />
  </div>
</template>

<style scoped>
.regulations-container {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xl);
}

.regulations-list {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--app-card-border);
  border-radius: var(--app-radius-lg);
  background: var(--app-card-bg);
  box-shadow: var(--app-card-shadow-rest);
  overflow: hidden;
}

.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-md);
  justify-content: flex-start;
}

@media (width <= 768px) {
  .list-header {
    flex-wrap: wrap;
  }
}
</style>
