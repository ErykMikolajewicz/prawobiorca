<script setup lang="ts">
import { computed, ref, onBeforeMount, watch } from 'vue'

import { storeToRefs } from 'pinia'

import AppNavbar from '@/components/organisms/AppNavbar.vue'
import AppFooter from '@/components/organisms/AppFooter.vue'
import PublicFilesList from '@/components/organisms/PublicRegulationsList.vue'
import UserRegulationsList from '@/components/organisms/UserRegulationsList.vue'
import UserCasesList from '@/components/organisms/UserCasesList.vue'
import RegulationUploadDialog from '@/components/molecules/RegulationUploadDialog.vue'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulations } from '@/api/generated/endpoints/user-regulations/user-regulations'
import { useRegulationsPolling } from '@/composables/useRegulationsPolling'

import type { regulationRepresentation, regulationType } from '@/types/api/regulations.ts'
import { getCasesList } from '@/api/generated/endpoints/cases/cases'
import type { caseData } from '@/types/api/cases.ts'

import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { isUserLogged, isAdmin } = storeToRefs(authStore)

const publicRegulations = ref<Array<regulationRepresentation>>([])

const userRegulations = ref<Array<regulationRepresentation>>([])

const cases = ref<Array<caseData>>([])

const isUploadDialogVisible = ref(false)

const publicRegulationTypeFilter = ref<regulationType | undefined>(undefined)
const userRegulationTypeFilter = ref<regulationType | undefined>(undefined)

function handleCaseCreated(newCase: caseData) {
  cases.value.push(newCase)
}

function handleRegulationCreated(regulation: regulationRepresentation, target: 'user' | 'public') {
  if (target === 'public') {
    publicRegulations.value.push(regulation)
  } else {
    userRegulations.value.push(regulation)
  }
}

function handleUserRegulationDeleted(regulationId: string) {
  userRegulations.value = userRegulations.value.filter(
    (regulation) => regulation.id !== regulationId,
  )
}

function handlePublicRegulationDeleted(regulationId: string) {
  publicRegulations.value = publicRegulations.value.filter(
    (regulation) => regulation.id !== regulationId,
  )
}

function handleUserRegulationPreparationRetried(regulationId: string) {
  markAsInProgress(userRegulations.value, regulationId)
}

function handlePublicRegulationPreparationRetried(regulationId: string) {
  markAsInProgress(publicRegulations.value, regulationId)
}

function markAsInProgress(regulations: Array<regulationRepresentation>, regulationId: string) {
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
    publicRegulations.value = []
  }
}

async function fetchUserRegulations() {
  try {
    userRegulations.value = await getUserRegulations({
      documentType: userRegulationTypeFilter.value,
    })
  } catch (error) {
    console.error('Failed to fetch user regulations:', error)
    userRegulations.value = []
  }
}

watch(publicRegulationTypeFilter, fetchPublicRegulations)
watch(userRegulationTypeFilter, fetchUserRegulations)

function isPending(regulation: regulationRepresentation): boolean {
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

      <PublicFilesList
        :regulations="publicRegulations"
        :type-filter="publicRegulationTypeFilter"
        :is-admin="isAdmin"
        @update:type-filter="(value) => (publicRegulationTypeFilter = value)"
        @regulation-deleted="handlePublicRegulationDeleted"
        @regulation-preparation-retried="handlePublicRegulationPreparationRetried"
      />

      <el-divider />

      <template v-if="isUserLogged">
        <UserRegulationsList
          :regulations="userRegulations"
          :type-filter="userRegulationTypeFilter"
          @update:type-filter="(value) => (userRegulationTypeFilter = value)"
          @user-regulation-deleted="handleUserRegulationDeleted"
          @user-regulation-preparation-retried="handleUserRegulationPreparationRetried"
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
