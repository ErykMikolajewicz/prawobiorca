<script setup lang="ts">
import { computed, reactive, ref, onBeforeMount } from 'vue'

import { storeToRefs } from 'pinia'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import RegulationsList from '@/components/organisms/RegulationsList.vue'
import UserCasesList from '@/components/organisms/UserCasesList.vue'
import RegulationUploadDialog from '@/components/molecules/RegulationUploadDialog.vue'
import { useRegulations } from '@/composables/useRegulations'
import { useRegulationsPolling } from '@/composables/useRegulationsPolling'

import type { CaseData, RegulationRepresentation } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'
import { getCasesList } from '@/api/generated/endpoints/cases/cases'

import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const { isUserLogged, isAdmin } = storeToRefs(authStore)

const publicRegulations = reactive(useRegulations('public'))
const userRegulations = reactive(useRegulations('user'))

const cases = ref<Array<CaseData>>([])

const isUploadDialogVisible = ref(false)

function handleCaseCreated(newCase: CaseData) {
  cases.value.push(newCase)
}

function handleCaseDeleted(caseId: string) {
  cases.value = cases.value.filter((c) => c.id !== caseId)
}

function handleRegulationCreated(regulation: RegulationRepresentation, target: RegulationScope) {
  if (target === 'public') {
    publicRegulations.add(regulation)
  } else {
    userRegulations.add(regulation)
  }
}

async function loadCases() {
  try {
    cases.value = await getCasesList()
  } catch (error) {
    showApiError(error, { defaultServerMessage: 'Nie udało się pobrać spraw.' })
  }
}

const hasPendingRegulations = computed(() => {
  if (isUserLogged.value && userRegulations.hasPending) {
    return true
  }
  return isAdmin.value && publicRegulations.hasPending
})

async function refreshRegulations() {
  try {
    await publicRegulations.fetch()

    if (isUserLogged.value) {
      await userRegulations.fetch()
    }
  } catch (error) {
    console.error('Failed to refresh regulations:', error)
  }
}

useRegulationsPolling(() => hasPendingRegulations.value, refreshRegulations)

onBeforeMount(async () => {
  await publicRegulations.load()

  if (isUserLogged.value) {
    await userRegulations.load()
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
      v-model:type-filter="publicRegulations.typeFilter"
      title="Publiczne regulacje"
      empty-description="Brak regulacji publicznych."
      :regulations="publicRegulations.regulations"
      target="public"
      :can-manage="isAdmin"
      @regulation-deleted="publicRegulations.remove"
      @regulation-preparation-retried="publicRegulations.markAsInProgress"
    />

    <el-divider />

    <template v-if="isUserLogged">
      <RegulationsList
        v-model:type-filter="userRegulations.typeFilter"
        title="Regulacje użytkownika"
        empty-description="Brak regulacji użytkownika."
        :regulations="userRegulations.regulations"
        target="user"
        can-manage
        @regulation-deleted="userRegulations.remove"
        @regulation-preparation-retried="userRegulations.markAsInProgress"
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
