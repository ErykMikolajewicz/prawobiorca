import { ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import { useOrganizationsStore } from '@/stores/organizations'
import {
  getPublishedApplicationTemplates,
  searchPublishedApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

export function usePublishedTemplates() {
  const templates = ref<Array<PublishedApplicationTemplate>>([])
  const query = ref('')
  const aiAssisted = ref(false)
  const searchResults = ref<Array<PublishedApplicationTemplate> | null>(null)

  const organizationsStore = useOrganizationsStore()
  let lastRequestId = 0
  let lastSearchRequestId = 0

  function getOrganizationParams() {
    return {
      organizationId: organizationsStore.selectedOrganizationId || undefined,
      suborganizationId: organizationsStore.selectedSuborganizationId || undefined,
    }
  }

  async function search(newQuery: string) {
    query.value = newQuery
    const requestId = ++lastSearchRequestId

    if (!newQuery.trim()) {
      searchResults.value = null
      return
    }

    try {
      const results = await searchPublishedApplicationTemplates({
        ...getOrganizationParams(),
        query: newQuery,
        aiAssisted: aiAssisted.value,
      })
      if (requestId === lastSearchRequestId) {
        searchResults.value = results
      }
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się wyszukać szablonów wniosków.' })
    }
  }

  async function load() {
    const requestId = ++lastRequestId
    try {
      const fetchedTemplates = await getPublishedApplicationTemplates(getOrganizationParams())
      if (requestId === lastRequestId) {
        templates.value = fetchedTemplates
      }
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonów wniosków.' })
      templates.value = []
    }
    await search(query.value)
  }

  watch(
    () => [organizationsStore.selectedOrganizationId, organizationsStore.selectedSuborganizationId],
    load,
  )

  watch(aiAssisted, () => search(query.value))

  return {
    templates,
    searchResults,
    aiAssisted,
    load,
    search,
  }
}
