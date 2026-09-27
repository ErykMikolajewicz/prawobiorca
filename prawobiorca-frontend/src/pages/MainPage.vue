<script setup lang="ts">
import { computed, ref, onBeforeMount, watch } from 'vue'

import { storeToRefs } from 'pinia'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
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

let publicRegulationsRequestId = 0
let userRegulationsRequestId = 0

async function fetchPublicRegulations() {
  const requestId = ++publicRegulationsRequestId
  const regulations = await getPublicRegulations({
    documentType: publicRegulationTypeFilter.value,
  })
  if (requestId === publicRegulationsRequestId) {
    publicRegulations.value = regulations
  }
}

async function fetchUserRegulations() {
  const requestId = ++userRegulationsRequestId
  const regulations = await getUserRegulations({
    documentType: userRegulationTypeFilter.value,
  })
  if (requestId === userRegulationsRequestId) {
    userRegulations.value = regulations
  }
}

async function fetchCases() {
  cases.value = await getCasesList()
}

async function loadWithErrorMessage(fetch: () => Promise<void>, errorMessage: string) {
  try {
    await fetch()
  } catch (error) {
    showApiError(error, { defaultServerMessage: errorMessage })
  }
}

async function loadPublicRegulations() {
  await loadWithErrorMessage(fetchPublicRegulations, 'Nie udało się pobrać regulacji publicznych.')
}

async function loadUserRegulations() {
  await loadWithErrorMessage(fetchUserRegulations, 'Nie udało się pobrać regulacji użytkownika.')
}

async function loadCases() {
  await loadWithErrorMessage(fetchCases, 'Nie udało się pobrać spraw.')
}

watch(publicRegulationTypeFilter, loadPublicRegulations)
watch(userRegulationTypeFilter, loadUserRegulations)

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
  try {
    await fetchPublicRegulations()

    if (isUserLogged.value) {
      await fetchUserRegulations()
    }
  } catch (error) {
    console.error('Failed to refresh regulations:', error)
  }
}

useRegulationsPolling(() => hasPendingRegulations.value, refreshRegulations)

onBeforeMount(async () => {
  await loadPublicRegulations()

  if (isUserLogged.value) {
    await loadUserRegulations()
    await loadCases()
  }
})
</script>

<template>
  <AppLayout>
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

    <RegulationUploadDialog
      v-model="isUploadDialogVisible"
      :is-admin="isAdmin"
      @created="handleRegulationCreated"
    />
  </AppLayout>
</template>

<style scoped>
.page-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 1rem;
}
</style>
