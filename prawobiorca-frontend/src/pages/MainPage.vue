<script setup lang="ts">
import { computed, reactive, ref, onBeforeMount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { storeToRefs } from 'pinia'

import AppLayout from '@/components/templates/AppLayout.vue'
import RegulationsList from '@/components/organisms/RegulationsList.vue'
import RegulationsSearchForm from '@/components/organisms/RegulationsSearchForm.vue'
import RegulationUploadDialog from '@/components/molecules/RegulationUploadDialog.vue'
import HowItWorks from '@/components/molecules/HowItWorks.vue'
import LoginCtaBanner from '@/components/molecules/LoginCtaBanner.vue'
import { useRegulations } from '@/composables/useRegulations'
import { usePendingPolling } from '@/composables/usePendingPolling'

import type { RegulationRepresentation } from '@/api/generated/model'
import type {
  RegulationScope,
  RegulationsOrder,
  RegulationsSearchParams,
} from '@/domain/regulations'
import { defaultThreshold } from '@/domain/search'

import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { isUserLogged, isAdmin } = storeToRefs(authStore)

const searchParams = ref<RegulationsSearchParams>({
  query: (route.query.query as string) || '',
  threshold: route.query.threshold !== undefined ? Number(route.query.threshold) : defaultThreshold,
  orderBy: (route.query.orderBy as RegulationsOrder) || 'name',
})

const publicRegulations = reactive(useRegulations('PUBLIC', () => searchParams.value))
const userRegulations = reactive(useRegulations('PRIVATE', () => searchParams.value))

const searchEmptyDescription = 'Brak regulacji pasujących do zapytania.'

async function loadRegulations() {
  await Promise.all([
    publicRegulations.load(),
    ...(isUserLogged.value ? [userRegulations.load()] : []),
  ])
}

async function handleSearch(newSearchParams: RegulationsSearchParams) {
  const isSearchChanged =
    newSearchParams.query !== searchParams.value.query ||
    newSearchParams.threshold !== searchParams.value.threshold

  searchParams.value = newSearchParams
  await router.replace({ query: newSearchParams.query ? newSearchParams : {} })

  if (isSearchChanged) {
    await loadRegulations()
  }
}

const isUploadDialogVisible = ref(false)

function handleRegulationCreated(regulation: RegulationRepresentation, target: RegulationScope) {
  if (target === 'PUBLIC') {
    publicRegulations.add(regulation)
  } else {
    userRegulations.add(regulation)
  }
}

const pendingRegulationIds = computed(() => [
  ...(isUserLogged.value ? userRegulations.pendingIds : []),
  ...(isAdmin.value ? publicRegulations.pendingIds : []),
])

async function refreshRegulations() {
  try {
    await Promise.all([
      publicRegulations.fetch(),
      ...(isUserLogged.value ? [userRegulations.fetch()] : []),
    ])
  } catch (error) {
    console.error('Failed to refresh regulations:', error)
  }
}

usePendingPolling(() => pendingRegulationIds.value, refreshRegulations)

onBeforeMount(loadRegulations)
</script>

<template>
  <AppLayout>
    <template v-if="!isUserLogged">
      <LoginCtaBanner />
      <HowItWorks />
    </template>

    <RegulationsSearchForm
      :search-params="searchParams"
      :can-use-advanced-threshold="isUserLogged"
      @search="handleSearch"
    />

    <el-divider />

    <RegulationsList
      v-model:type-filter="publicRegulations.typeFilter"
      title="Publiczne regulacje"
      :empty-description="
        searchParams.query ? searchEmptyDescription : 'Brak regulacji publicznych.'
      "
      :regulations="publicRegulations.regulations"
      :scores="publicRegulations.scores"
      :loading="publicRegulations.isLoading"
      target="PUBLIC"
      :can-manage="isAdmin"
      @regulation-updated="publicRegulations.update"
      @regulation-deleted="publicRegulations.remove"
      @regulation-preparation-retried="publicRegulations.markAsInProgress"
      @regulation-description-generation-started="publicRegulations.markDescriptionAsInProgress"
    >
      <template v-if="isUserLogged" #actions>
        <el-button type="primary" @click="isUploadDialogVisible = true">Dodaj regulacje</el-button>
      </template>
    </RegulationsList>

    <el-divider />

    <template v-if="isUserLogged">
      <RegulationsList
        v-model:type-filter="userRegulations.typeFilter"
        title="Regulacje użytkownika"
        :empty-description="
          searchParams.query ? searchEmptyDescription : 'Brak regulacji użytkownika.'
        "
        :regulations="userRegulations.regulations"
        :scores="userRegulations.scores"
        :loading="userRegulations.isLoading"
        target="PRIVATE"
        can-manage
        @regulation-updated="userRegulations.update"
        @regulation-deleted="userRegulations.remove"
        @regulation-preparation-retried="userRegulations.markAsInProgress"
        @regulation-description-generation-started="userRegulations.markDescriptionAsInProgress"
      />
    </template>

    <RegulationUploadDialog
      v-model="isUploadDialogVisible"
      :is-admin="isAdmin"
      @created="handleRegulationCreated"
    />
  </AppLayout>
</template>
