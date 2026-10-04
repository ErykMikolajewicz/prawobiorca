<script setup lang="ts">
import { storeToRefs } from 'pinia'
import { useRoute, useRouter } from 'vue-router'
import SidebarCaseItem from '@/components/molecules/SidebarCaseItem.vue'
import CaseCreationCard from '@/components/molecules/CaseCreationCard.vue'
import { useCasesStore } from '@/stores/cases'

const route = useRoute()
const router = useRouter()
const casesStore = useCasesStore()
const { cases, activeCaseId } = storeToRefs(casesStore)

async function handleCaseDeleted(caseId: string) {
  casesStore.remove(caseId)
  if (route.name === 'CasePage' && route.params.id === caseId) {
    await router.push({ name: 'MainPage' })
  }
}
</script>

<template>
  <div class="sidebar-cases-list">
    <CaseCreationCard @case-created="casesStore.add" />

    <h2 class="cases-title">Moje sprawy</h2>

    <div class="cases-items">
      <SidebarCaseItem
        v-for="userCase in cases"
        :key="userCase.id"
        :user-case="userCase"
        :is-active="userCase.id === activeCaseId"
        @deleted="handleCaseDeleted"
        @activate="casesStore.setActive"
      />
    </div>
  </div>
</template>

<style scoped>
.sidebar-cases-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-height: 0;
}

.cases-title {
  margin: 0;
  padding-left: var(--el-menu-base-level-padding);
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--el-text-color-secondary);
}

.cases-items {
  overflow-y: auto;
  min-height: 0;
}
</style>
