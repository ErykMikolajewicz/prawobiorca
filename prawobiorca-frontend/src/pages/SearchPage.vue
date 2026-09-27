<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import { ArrowLeft } from '@element-plus/icons-vue'

import AppLayout from '@/components/templates/AppLayout.vue'
import SearchForm from '@/components/organisms/SearchForm.vue'
import CaseSelector from '@/components/molecules/CaseSelector.vue'
import SearchResultsList from '@/components/organisms/SearchResultsList.vue'

import { useAuthStore } from '@/stores/auth'
import { addCaseDocument, getCasesList } from '@/api/generated/endpoints/cases/cases'
import type {
  CaseData,
  SearchOrder,
  SearchRegulationDocumentsParams,
  SearchResult,
} from '@/api/generated/model'
import { searchRegulationDocuments } from '@/api/generated/endpoints/regulations/regulations'
import { searchUserRegulationDocuments } from '@/api/generated/endpoints/user-regulations/user-regulations'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { isUserLogged } = storeToRefs(authStore)

const regulationId = ref((route.params.regulationId as string) || '')
const regulationName = history.state.filename
const searchParams = ref<SearchRegulationDocumentsParams>({
  query: (route.query.query as string) || '',
  threshold: route.query.threshold !== undefined ? Number(route.query.threshold) : 0.2,
  limit: route.query.limit ? Number(route.query.limit) : undefined,
  order_by: (route.query.order_by as SearchOrder) || 'document',
})

const cases = ref<Array<CaseData>>([])
const selectedCaseId = ref<string>('')
const results = ref<Array<SearchResult>>([])
const isSearching = ref(false)

onBeforeMount(async () => {
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

const handleSearch = async (newSearchParams: SearchRegulationDocumentsParams) => {
  searchParams.value = newSearchParams

  await router.replace({
    query: newSearchParams,
  })

  await performSearch(newSearchParams)
}

async function performSearch(params: SearchRegulationDocumentsParams) {
  isSearching.value = true

  const isUserFile = route.path.includes('/user/regulations')
  try {
    if (isUserFile) {
      results.value = await searchUserRegulationDocuments(regulationId.value, params)
    } else {
      results.value = await searchRegulationDocuments(regulationId.value, params)
    }
  } catch (error) {
    showApiError(error, { defaultServerMessage: 'Wystąpił błąd podczas przeszukiwania regulacji.' })
  } finally {
    isSearching.value = false
  }
}

async function handleAddToCase(payload: { documentContent: string }) {
  if (!selectedCaseId.value) {
    ElMessage.warning('Wybierz sprawę z listy.')
    return
  }

  try {
    await addCaseDocument(selectedCaseId.value, {
      presentationName: regulationName,
      content: payload.documentContent,
    })
    ElMessage.success('Dodano do sprawy.')
  } catch (error) {
    showApiError(error, { defaultServerMessage: 'Wystąpił błąd podczas dodawania do sprawy.' })
  }
}
</script>

<template>
  <AppLayout>
    <el-button link @click="router.push('/')">
      <el-icon><ArrowLeft /></el-icon> Powrót do głównego ekranu
    </el-button>

    <CaseSelector v-model:selected-case-id="selectedCaseId" :cases="cases" />

    <h1>Przeszukaj regulacje: {{ regulationName }}</h1>

    <div v-loading="isSearching">
      <SearchForm :search-params="searchParams" @search="handleSearch" />

      <SearchResultsList
        :results="results"
        :selected-case-id="selectedCaseId"
        :query="searchParams.query"
        @add-to-case="handleAddToCase"
      />
    </div>
  </AppLayout>
</template>
