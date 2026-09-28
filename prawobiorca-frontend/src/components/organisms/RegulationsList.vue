<script setup lang="ts">
import { computed } from 'vue'
import RegulationCard from '@/components/molecules/RegulationCard.vue'
import RegulationTypeFilter from '@/components/molecules/RegulationTypeFilter.vue'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

type Props = {
  title: string
  emptyDescription: string
  regulations: Array<RegulationRepresentation>
  target: RegulationScope
  canManage: boolean
}

const props = defineProps<Props>()

const typeFilter = defineModel<RegulationType | undefined>('typeFilter')

const emit = defineEmits<{
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
      <RegulationTypeFilter v-model="typeFilter" />
    </div>

    <div v-if="displayedRegulations.length" class="cards-grid">
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

.filter-row {
  display: flex;
  justify-content: flex-start;
}
</style>
