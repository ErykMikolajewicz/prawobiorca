import { computed, ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulations } from '@/api/generated/endpoints/user-regulations/user-regulations'
import { isPending, type RegulationScope } from '@/domain/regulations'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'

const loadErrorMessages: Record<RegulationScope, string> = {
  public: 'Nie udało się pobrać regulacji publicznych.',
  user: 'Nie udało się pobrać regulacji użytkownika.',
}

export function useRegulations(scope: RegulationScope) {
  const regulations = ref<Array<RegulationRepresentation>>([])
  const typeFilter = ref<RegulationType | undefined>(undefined)
  const isLoading = ref(false)
  const pendingIds = computed(() =>
    regulations.value.filter(isPending).map((regulation) => regulation.id),
  )

  const getRegulations = scope === 'public' ? getPublicRegulations : getUserRegulations
  let lastRequestId = 0

  async function fetch() {
    const requestId = ++lastRequestId
    const fetchedRegulations = await getRegulations({ documentType: typeFilter.value })
    if (requestId === lastRequestId) {
      regulations.value = fetchedRegulations
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
    regulations.value.push(regulation)
  }

  function remove(regulationId: string) {
    regulations.value = regulations.value.filter((regulation) => regulation.id !== regulationId)
  }

  function markAsInProgress(regulationId: string) {
    const regulation = regulations.value.find((item) => item.id === regulationId)
    if (regulation) {
      regulation.preparationStatus = 'IN_PROGRESS'
    }
  }

  watch(typeFilter, load)

  return {
    regulations,
    typeFilter,
    isLoading,
    pendingIds,
    fetch,
    load,
    add,
    remove,
    markAsInProgress,
  }
}
