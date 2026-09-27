<script setup lang="ts">
import { computed, ref, onBeforeMount, watch } from 'vue'

import { storeToRefs } from 'pinia'

import AppNavbar from '@/components/organisms/AppNavbar.vue'
import AppFooter from '@/components/organisms/AppFooter.vue'
import RegulationsList from '@/components/organisms/RegulationsList.vue'
import UserCasesList from '@/components/organisms/UserCasesList.vue'
import RegulationUploadDialog from '@/components/molecules/RegulationUploadDialog.vue'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulations } from '@/api/generated/endpoints/user-regulations/user-regulations'
import { useRegulationsPolling } from '@/composables/useRegulationsPolling'

import type { CaseData, RegulationRepresentation, RegulationType } from '@/api/generated/model'
import { getCasesList } from '@/api/generated/endpoints/cases/cases'

import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { isUserLogged, isAdmin } = storeToRefs(authStore)

const publicRegulations = ref<Array<RegulationRepresentation>>([])

const userRegulations = ref<Array<RegulationRepresentation>>([])

const cases = ref<Array<CaseData>>([])

const isUploadDialogVisible = ref(false)

const publicRegulationTypeFilter = ref<RegulationType | undefined>(undefined)
const userRegulationTypeFilter = ref<RegulationType | undefined>(undefined)

function handleCaseCreated(newCase: CaseData) {
  cases.value.push(newCase)
}

function handleRegulationCreated(regulation: RegulationRepresentation, target: 'user' | 'public') {
  if (target === 'public') {
    publicRegulations.value.push(regulation)
  } else {
    userRegulations.value.push(regulation)
  }
}

function removeRegulation(regulations: Array<RegulationRepresentation>, regulationId: string) {
  const index = regulations.findIndex((item) => item.id === regulationId)
  if (index !== -1) {
    regulations.splice(index, 1)
  }
}

function markAsInProgress(regulations: Array<RegulationRepresentation>, regulationId: string) {
  const regulation = regulations.find((item) => item.id === regulationId)
  if (regulation) {
    regulation.preparationStatus = 'IN_PROGRESS'
  }
}

function handleCaseDeleted(caseId: string) {
  cases.value = cases.value.filter((c) => c.id !== caseId)
}

async function fetchPublicRegulations() {
  try {
    publicRegulations.value = await getPublicRegulations({
      documentType: publicRegulationTypeFilter.value,
    })
  } catch (error) {
    console.error('Failed to fetch public files:', error)
  }
}

async function fetchUserRegulations() {
  try {
    userRegulations.value = await getUserRegulations({
      documentType: userRegulationTypeFilter.value,
    })
  } catch (error) {
    console.error('Failed to fetch user regulations:', error)
  }
}

watch(publicRegulationTypeFilter, fetchPublicRegulations)
watch(userRegulationTypeFilter, fetchUserRegulations)

function isPending(regulation: RegulationRepresentation): boolean {
  return (
    regulation.preparationStatus === 'NOT_STARTED' || regulation.preparationStatus === 'IN_PROGRESS'
  )
}

const hasPendingRegulations = computed(() => {
  if (isUserLogged.value && userRegulations.value.some(isPending)) {
    return true
  }
  return isAdmin.value && publicRegulations.value.some(isPending)
})

async function refreshRegulations() {
  await fetchPublicRegulations()

  if (isUserLogged.value) {
    await fetchUserRegulations()
  }
}

useRegulationsPolling(() => hasPendingRegulations.value, refreshRegulations)

onBeforeMount(async () => {
  await fetchPublicRegulations()

  if (isUserLogged.value) {
    try {
      await fetchUserRegulations()
      cases.value = await getCasesList()
    } catch (error) {
      console.error('Failed to fetch user data:', error)
      cases.value = []
    }
  }
})
</script>

<template>
  <div class="page-container">
    <AppNavbar />

    <main class="main-content">
      <div v-if="isUserLogged" class="page-actions">
        <el-button type="primary" @click="isUploadDialogVisible = true">Dodaj plik</el-button>
      </div>

      <RegulationsList
        v-model:type-filter="publicRegulationTypeFilter"
        title="Publiczne regulacje"
        empty-description="Brak regulacji publicznych."
        :regulations="publicRegulations"
        target="public"
        :can-manage="isAdmin"
        @regulation-deleted="(regulationId) => removeRegulation(publicRegulations, regulationId)"
        @regulation-preparation-retried="
          (regulationId) => markAsInProgress(publicRegulations, regulationId)
        "
      />

      <el-divider />

      <template v-if="isUserLogged">
        <RegulationsList
          v-model:type-filter="userRegulationTypeFilter"
          title="Regulacje użytkownika"
          empty-description="Brak regulacji użytkownika."
          :regulations="userRegulations"
          target="user"
          :can-manage="true"
          @regulation-deleted="(regulationId) => removeRegulation(userRegulations, regulationId)"
          @regulation-preparation-retried="
            (regulationId) => markAsInProgress(userRegulations, regulationId)
          "
        />

        <el-divider />

        <UserCasesList
          :cases="cases"
          @case-deleted="handleCaseDeleted"
          @case-created="handleCaseCreated"
        />
      </template>
    </main>

    <RegulationUploadDialog
      v-model="isUploadDialogVisible"
      :is-admin="isAdmin"
      @created="handleRegulationCreated"
    />

    <AppFooter />
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  flex-grow: 1;
  padding: 1rem;
  width: 100%;
  max-width: 1200px;
  box-sizing: border-box;
  overflow-x: hidden;
}

.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}

@media (max-width: 768px) {
  .main-content {
    padding: 0.5rem;
  }
}
</style>
