import { ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import { useOrganizationsStore } from '@/stores/organizations'
import {
  getPublishedApplicationTemplates,
  searchPublishedApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'
import type { PublishedApplicationTemplate } from '@/api/generated/model'
import { defaultThreshold } from '@/domain/search'

export function usePublishedTemplates() {
  const templates = ref<Array<PublishedApplicationTemplate>>([])
  const query = ref('')
  const scores = ref<Record<string, number> | null>(null)
  const searching = ref(false)

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

    if (!newQuery) {
      scores.value = null
      searching.value = false
      return
    }

    searching.value = true
    try {
      const results = await searchPublishedApplicationTemplates({
        ...getOrganizationParams(),
        query: newQuery,
        threshold: defaultThreshold,
      })
      if (requestId === lastSearchRequestId) {
        scores.value = Object.fromEntries(
          results.map((result) => [result.template.id, result.score]),
        )
      }
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się wyszukać szablonów wniosków.' })
    } finally {
      if (requestId === lastSearchRequestId) {
        searching.value = false
      }
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

  return {
    templates,
    scores,
    searching,
    load,
    search,
  }
}
