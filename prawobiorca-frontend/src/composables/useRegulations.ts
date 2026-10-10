import { computed, ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import { getPublicRegulations } from '@/api/generated/endpoints/regulations/regulations'
import { getUserRegulations } from '@/api/generated/endpoints/user-regulations/user-regulations'
import { useOrganizationsStore } from '@/stores/organizations'
import type { RegulationScope } from '@/domain/regulations'
import type { RegulationRepresentation, RegulationType } from '@/api/generated/model'

const loadErrorMessages: Record<RegulationScope, string> = {
  public: 'Nie udało się pobrać regulacji publicznych.',
  user: 'Nie udało się pobrać regulacji użytkownika.',
}

function isPending(regulation: RegulationRepresentation): boolean {
  return regulation.preparationStatus === 'IN_PROGRESS'
}

export function useRegulations(scope: RegulationScope) {
  const regulations = ref<Array<RegulationRepresentation>>([])
  const typeFilter = ref<RegulationType | undefined>(undefined)
  const isLoading = ref(false)
  const pendingIds = computed(() =>
    regulations.value.filter(isPending).map((regulation) => regulation.id),
  )

  const organizationsStore = useOrganizationsStore()
  let lastRequestId = 0

  function getRegulations() {
    if (scope === 'user') {
      return getUserRegulations({ documentType: typeFilter.value })
    }
    return getPublicRegulations({
      documentType: typeFilter.value,
      organizationId: organizationsStore.selectedOrganizationId || undefined,
      suborganizationId: organizationsStore.selectedSuborganizationId || undefined,
    })
  }

  async function fetch() {
    const requestId = ++lastRequestId
    const fetchedRegulations = await getRegulations()
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

  function update(updatedRegulation: RegulationRepresentation) {
    regulations.value = regulations.value.map((regulation) =>
      regulation.id === updatedRegulation.id ? updatedRegulation : regulation,
    )
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
  if (scope === 'public') {
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
    typeFilter,
    isLoading,
    pendingIds,
    fetch,
    load,
    add,
    update,
    remove,
    markAsInProgress,
  }
}
