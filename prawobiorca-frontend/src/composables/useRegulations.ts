import { computed, ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import {
  getRegulations as getRegulationsByScope,
  searchRegulations,
} from '@/api/generated/endpoints/regulations/regulations'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationScope, RegulationsSearchParams } from '@/domain/regulations'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'

const loadErrorMessages: Record<RegulationScope, string> = {
  PUBLIC: 'Nie udało się pobrać regulacji publicznych.',
  PRIVATE: 'Nie udało się pobrać regulacji użytkownika.',
}

function isPending(regulation: RegulationRepresentation): boolean {
  return (
    regulation.preparationStatus === 'IN_PROGRESS' ||
    (regulation.preparationStatus === 'PREPARED' && regulation.descriptionStatus === 'IN_PROGRESS')
  )
}

function sortByName(regulations: Array<RegulationRepresentation>): Array<RegulationRepresentation> {
  const sortedRegulations = [...regulations]
  sortedRegulations.sort((a, b) => a.presentationName.localeCompare(b.presentationName, 'pl'))
  return sortedRegulations
}

export function useRegulations(
  scope: RegulationScope,
  searchParams: () => RegulationsSearchParams,
) {
  const fetchedRegulations = ref<Array<RegulationRepresentation>>([])
  const scores = ref<Record<string, number>>({})
  const typeFilter = ref<RegulationType | undefined>(undefined)
  const isLoading = ref(false)
  const pendingIds = computed(() =>
    fetchedRegulations.value.filter(isPending).map((regulation) => regulation.id),
  )

  const regulations = computed(() => {
    const { query, orderBy } = searchParams()
    if (!query) {
      return sortByName(fetchedRegulations.value)
    }

    const scoredRegulations = fetchedRegulations.value.filter(
      (regulation) => regulation.id in scores.value,
    )
    if (orderBy === 'score') {
      return scoredRegulations
    }
    return sortByName(scoredRegulations)
  })

  const organizationsStore = useOrganizationsStore()
  let lastRequestId = 0

  function getFilterParams() {
    if (scope === 'PRIVATE') {
      return { scope, documentType: typeFilter.value }
    }
    return {
      scope,
      documentType: typeFilter.value,
      organizationId: organizationsStore.selectedOrganizationId || undefined,
      suborganizationId: organizationsStore.selectedSuborganizationId || undefined,
    }
  }

  async function fetch() {
    const requestId = ++lastRequestId
    const { query, threshold } = searchParams()

    if (!query) {
      const foundRegulations = await getRegulationsByScope(getFilterParams())
      if (requestId === lastRequestId) {
        fetchedRegulations.value = foundRegulations
        scores.value = {}
      }
      return
    }

    const results = await searchRegulations({ ...getFilterParams(), query, threshold })
    if (requestId === lastRequestId) {
      fetchedRegulations.value = results.map((result) => result.regulation)
      scores.value = Object.fromEntries(
        results.map((result) => [result.regulation.id, result.score]),
      )
    }
  }

  async function load() {
    isLoading.value = true
    try {
      await fetch()
    } catch (error) {
      showApiError(error, { defaultMessage: loadErrorMessages[scope] })
    } finally {
      isLoading.value = false
    }
  }

  function add(regulation: RegulationRepresentation) {
    fetchedRegulations.value.push(regulation)
  }

  function update(updatedRegulation: RegulationRepresentation) {
    fetchedRegulations.value = fetchedRegulations.value.map((regulation) =>
      regulation.id === updatedRegulation.id ? updatedRegulation : regulation,
    )
  }

  function remove(regulationId: string) {
    fetchedRegulations.value = fetchedRegulations.value.filter(
      (regulation) => regulation.id !== regulationId,
    )
  }

  function markAsInProgress(regulationId: string) {
    const regulation = fetchedRegulations.value.find((item) => item.id === regulationId)
    if (regulation) {
      regulation.preparationStatus = 'IN_PROGRESS'
    }
  }

  function markDescriptionAsInProgress(regulationId: string) {
    const regulation = fetchedRegulations.value.find((item) => item.id === regulationId)
    if (regulation) {
      regulation.descriptionStatus = 'IN_PROGRESS'
    }
  }

  watch(typeFilter, load)
  if (scope === 'PUBLIC') {
    watch(
      () => [
        organizationsStore.selectedOrganizationId,
        organizationsStore.selectedSuborganizationId,
      ],
      load,
    )
  }

  return {
    regulations,
    scores,
    typeFilter,
    isLoading,
    pendingIds,
    fetch,
    load,
    add,
    update,
    remove,
    markAsInProgress,
    markDescriptionAsInProgress,
  }
}
