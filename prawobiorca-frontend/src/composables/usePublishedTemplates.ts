import { ref, watch } from 'vue'
import { showApiError } from '@/utils/error'
import { useOrganizationsStore } from '@/stores/organizations'
import { getPublishedApplicationTemplates } from '@/api/generated/endpoints/application-templates/application-templates'
import type { PublishedApplicationTemplate } from '@/api/generated/model'

export function usePublishedTemplates() {
  const templates = ref<Array<PublishedApplicationTemplate>>([])

  const organizationsStore = useOrganizationsStore()
  let lastRequestId = 0

  async function load() {
    const requestId = ++lastRequestId
    try {
      const fetchedTemplates = await getPublishedApplicationTemplates({
        organizationId: organizationsStore.selectedOrganizationId || undefined,
        suborganizationId: organizationsStore.selectedSuborganizationId || undefined,
      })
      if (requestId === lastRequestId) {
        templates.value = fetchedTemplates
      }
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonów wniosków.' })
      templates.value = []
    }
  }

  watch(
    () => [organizationsStore.selectedOrganizationId, organizationsStore.selectedSuborganizationId],
    load,
  )

  return {
    templates,
    load,
  }
}
