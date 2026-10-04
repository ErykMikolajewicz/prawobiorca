<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import BackToMainButton from '@/components/atoms/BackToMainButton.vue'
import SearchForm from '@/components/organisms/SearchForm.vue'
import CaseSelector from '@/components/molecules/CaseSelector.vue'
import SearchResultsList from '@/components/organisms/SearchResultsList.vue'
import { useRegulationSearch } from '@/composables/useRegulationSearch'

import { useAuthStore } from '@/stores/auth'
import { addCaseDocument, getCasesList } from '@/api/generated/endpoints/cases/cases'
import type { CaseData, SearchOrder, SearchRegulationDocumentsParams } from '@/api/generated/model'
import { getPublicRegulation } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulation } from '@/api/generated/endpoints/user-regulations/user-regulations'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { isUserLogged } = storeToRefs(authStore)

const regulationId = route.params.regulationId as string
const isUserRegulation = route.name === 'SearchUserRegulation'
const regulationName = ref('')
const searchParams = ref<SearchRegulationDocumentsParams>({
  query: (route.query.query as string) || '',
  threshold: route.query.threshold !== undefined ? Number(route.query.threshold) : 0.2,
  limit: route.query.limit ? Number(route.query.limit) : undefined,
  order_by: (route.query.order_by as SearchOrder) || 'document',
})

const cases = ref<Array<CaseData>>([])
const selectedCaseId = ref<string>('')
const {
  results,
  isSearching,
  search: performSearch,
} = useRegulationSearch(isUserRegulation ? 'user' : 'public', regulationId)

onBeforeMount(async () => {
  void loadRegulationName()

  if (searchParams.value.query) {
    void performSearch(searchParams.value)
  }

  if (isUserLogged.value) {
    try {
      cases.value = await getCasesList()
    } catch (error) {
      console.error('Failed to fetch cases:', error)
      cases.value = []
    }
  }
})

async function loadRegulationName() {
  const getRegulation = isUserRegulation ? getUserRegulation : getPublicRegulation
  try {
    const regulation = await getRegulation(regulationId)
    regulationName.value = regulation.presentationName
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać regulacji.' })
  }
}

async function handleSearch(newSearchParams: SearchRegulationDocumentsParams) {
  searchParams.value = newSearchParams

  await router.replace({
    query: newSearchParams,
  })

  await performSearch(newSearchParams)
}

async function handleAddToCase(payload: { documentContent: string; header: string | null }) {
  if (!selectedCaseId.value) {
    ElMessage.warning('Wybierz sprawę z listy.')
    return
  }

  try {
    await addCaseDocument(selectedCaseId.value, {
      presentationName: regulationName.value,
      content: payload.documentContent,
      header: payload.header,
    })
    ElMessage.success('Dodano do sprawy.')
  } catch (error) {
    showApiError(error, { defaultMessage: 'Wystąpił błąd podczas dodawania do sprawy.' })
  }
}
</script>

<template>
  <AppLayout>
    <BackToMainButton />

    <CaseSelector v-if="isUserLogged" v-model:selected-case-id="selectedCaseId" :cases="cases" />

    <h1>Przeszukaj regulacje: {{ regulationName }}</h1>

    <div v-loading="isSearching">
      <SearchForm :search-params="searchParams" @search="handleSearch" />

      <SearchResultsList
        :results="results"
        :selected-case-id="selectedCaseId"
        :can-add-to-case="isUserLogged"
        :query="searchParams.query"
        @add-to-case="handleAddToCase"
      />
    </div>

    <el-backtop />
  </AppLayout>
</template>
