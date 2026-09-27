<script setup lang="ts">
import { computed } from 'vue'
import RegulationCard from '@/components/molecules/RegulationCard.vue'
import RegulationTypeFilter from '@/components/molecules/RegulationTypeFilter.vue'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'
import type { uploadTarget } from '@/composables/useRegulationUpload'

type Props = {
  title: string
  emptyDescription: string
  regulations: Array<RegulationRepresentation>
  typeFilter: RegulationType | undefined
  target: uploadTarget
  canManage: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:typeFilter', value: RegulationType | undefined): void
  (e: 'regulation-deleted', regulationId: string): void
  (e: 'regulation-preparation-retried', regulationId: string): void
}>()

const displayedRegulations = computed(() => {
  if (props.canManage) {
    return props.regulations
  }
  return props.regulations.filter((regulation) => regulation.preparationStatus === 'PREPARED')
})
</script>

<template>
  <div class="regulations-container">
    <h2 class="section-title">{{ title }}</h2>

    <div class="filter-row">
      <RegulationTypeFilter
        :model-value="typeFilter"
        @update:model-value="(value) => emit('update:typeFilter', value)"
      />
    </div>

    <div v-if="displayedRegulations.length" class="files-grid">
      <RegulationCard
        v-for="regulation in displayedRegulations"
        :key="regulation.id"
        :regulation="regulation"
        :target="target"
        :can-manage="canManage"
        @deleted="(regulationId) => emit('regulation-deleted', regulationId)"
        @preparation-retried="
          (regulationId) => emit('regulation-preparation-retried', regulationId)
        "
      />
    </div>

    <el-empty v-else :description="emptyDescription" />
  </div>
</template>

<style scoped>
.regulations-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--el-text-color-primary);
  padding-left: 12px;
  border-left: 4px solid var(--el-color-primary);
}

.filter-row {
  display: flex;
  justify-content: flex-start;
}

.files-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 300px), 1fr));
}
</style>
