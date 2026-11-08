import { ref } from 'vue'
import { showApiError } from '@/utils/error'
import { searchRegulationDocuments } from '@/api/generated/endpoints/regulations/regulations'
import type { SearchRegulationDocumentsParams, SearchResult } from '@/api/generated/model'

export function useRegulationSearch(regulationId: string) {
  const results = ref<Array<SearchResult>>([])
  const isSearching = ref(false)
  let lastRequestId = 0

  async function search(params: SearchRegulationDocumentsParams) {
    const requestId = ++lastRequestId
    isSearching.value = true

    try {
      const foundResults = await searchRegulationDocuments(regulationId, params)
      if (requestId === lastRequestId) {
        results.value = foundResults
      }
    } catch (error) {
      if (requestId === lastRequestId) {
        showApiError(error, { defaultMessage: 'Wystąpił błąd podczas przeszukiwania regulacji.' })
      }
    } finally {
      if (requestId === lastRequestId) {
        isSearching.value = false
      }
    }
  }

  return { results, isSearching, search }
}
