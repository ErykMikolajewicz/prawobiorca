<script setup lang="ts">
import CaseCard from '@/components/molecules/CaseCard.vue'
import CaseCreationCard from '@/components/molecules/CaseCreationCard.vue'
import type { CaseData } from '@/api/generated/model'

type Props = {
  cases: Array<CaseData>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'case-deleted', caseId: string): void
  (e: 'case-created', newCase: CaseData): void
}>()
</script>

<template>
  <div class="user-cases-container">
    <h2 class="section-title">Moje sprawy</h2>

    <div class="cards-grid">
      <CaseCard
        v-for="userCase in props.cases"
        :key="userCase.id"
        :user-case="userCase"
        @deleted="(id) => emit('case-deleted', id)"
      />

      <CaseCreationCard @case-created="(newCase) => emit('case-created', newCase)" />
    </div>
  </div>
</template>

<style scoped>
.user-cases-container {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}
</style>
