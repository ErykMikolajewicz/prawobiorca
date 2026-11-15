import { ref } from 'vue'
import { showApiError } from '@/utils/error'
import {
  listRegulationSections,
  searchRegulationDocuments,
} from '@/api/generated/endpoints/regulations/regulations'
import type { SearchOrder, SearchRegulationDocumentsParams } from '@/api/generated/model'
import type { RegulationSearchResult } from '@/utils/searchResults'

const SCORE_ORDER_DEFAULT_LIMIT = 10

export function defaultSearchLimit(order: SearchOrder): number | undefined {
  return order === 'score' ? SCORE_ORDER_DEFAULT_LIMIT : undefined
}

export function useRegulationSearch(regulationId: string) {
  const results = ref<Array<RegulationSearchResult>>([])
  const isSearching = ref(false)
  let lastRequestId = 0

  async function load(request: () => Promise<Array<RegulationSearchResult>>, errorMessage: string) {
    const requestId = ++lastRequestId
    isSearching.value = true

    try {
      const foundResults = await request()
      if (requestId === lastRequestId) {
        results.value = foundResults
      }
    } catch (error) {
      if (requestId === lastRequestId) {
        showApiError(error, { defaultMessage: errorMessage })
      }
    } finally {
      if (requestId === lastRequestId) {
        isSearching.value = false
      }
    }
  }

  function search(params: SearchRegulationDocumentsParams) {
    return load(
      () => searchRegulationDocuments(regulationId, params),
      'Wystąpił błąd podczas przeszukiwania regulacji.',
    )
  }

  function browse() {
    return load(
      () => listRegulationSections(regulationId),
      'Wystąpił błąd podczas pobierania treści regulacji.',
    )
  }

  return { results, isSearching, search, browse }
}
