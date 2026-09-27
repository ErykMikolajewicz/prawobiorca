<script setup lang="ts">
import UserRegulationCard from '@/components/molecules/UserRegulationCard.vue'
import RegulationTypeFilter from '@/components/molecules/RegulationTypeFilter.vue'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'

type Props = {
  regulations: Array<RegulationRepresentation>
  typeFilter: RegulationType | undefined
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'user-regulation-deleted', regulationId: string): void
  (e: 'user-regulation-preparation-retried', regulationId: string): void
  (e: 'update:typeFilter', value: RegulationType | undefined): void
}>()
</script>

<template>
  <div class="user-files-container">
    <h2 class="section-title">Regulacje użytkownika</h2>

    <div class="filter-row">
      <RegulationTypeFilter
        :model-value="typeFilter"
        @update:model-value="(value) => emit('update:typeFilter', value)"
      />
    </div>

    <div v-if="regulations.length" class="files-grid">
      <UserRegulationCard
        v-for="regulation in regulations"
        :key="regulation.id"
        :regulation="regulation"
        @deleted="(regulationId) => emit('user-regulation-deleted', regulationId)"
        @preparation-retried="
          (regulationId) => emit('user-regulation-preparation-retried', regulationId)
        "
      />
    </div>

    <el-empty v-else description="Brak regulacji użytkownika." />
  </div>
</template>

<style scoped>
.user-files-container {
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
