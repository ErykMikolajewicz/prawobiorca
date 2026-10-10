import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getOrganizations } from '@/api/generated/endpoints/organizations/organizations'
import type { OrganizationData } from '@/api/generated/model'
import { useAuthStore } from '@/stores/auth'
import { showApiError } from '@/utils/error'

const SELECTED_ORGANIZATION_STORAGE_KEY = 'selected-organization'

type StoredSelection = {
  organizationId: string
  suborganizationId: string
}

function readStoredSelection(): StoredSelection | null {
  const stored = localStorage.getItem(SELECTED_ORGANIZATION_STORAGE_KEY)
  if (stored === null) {
    return null
  }
  try {
    return JSON.parse(stored) as StoredSelection
  } catch {
    return null
  }
}

export const useOrganizationsStore = defineStore('organizations', () => {
  const authStore = useAuthStore()
  const organizations = ref<Array<OrganizationData>>([])
  const selectedOrganizationId = ref<string>('')
  const selectedSuborganizationId = ref<string>('')
  const selectedOrganization = computed(() =>
    organizations.value.find((o) => o.id === selectedOrganizationId.value),
  )
  const selectedSuborganization = computed(() =>
    selectedOrganization.value?.suborganizations.find(
      (s) => s.id === selectedSuborganizationId.value,
    ),
  )

  function select(organizationId: string, suborganizationId: string): void {
    selectedOrganizationId.value = organizationId
    selectedSuborganizationId.value = suborganizationId
    localStorage.setItem(
      SELECTED_ORGANIZATION_STORAGE_KEY,
      JSON.stringify({ organizationId, suborganizationId }),
    )
  }

  async function load(): Promise<void> {
    try {
      organizations.value = await getOrganizations()
      const defaultOrganizationId = authStore.isUserLogged ? (organizations.value[0]?.id ?? '') : ''
      const storedSelection = readStoredSelection()
      if (storedSelection === null) {
        selectedOrganizationId.value = defaultOrganizationId
        selectedSuborganizationId.value = ''
        return
      }
      const storedOrganization = organizations.value.find(
        (o) => o.id === storedSelection.organizationId,
      )
      const storedSuborganization = storedOrganization?.suborganizations.find(
        (s) => s.id === storedSelection.suborganizationId,
      )
      selectedOrganizationId.value =
        storedSelection.organizationId === ''
          ? ''
          : (storedOrganization?.id ?? defaultOrganizationId)
      selectedSuborganizationId.value = storedSuborganization?.id ?? ''
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać organizacji.' })
    }
  }

  return {
    organizations,
    selectedOrganizationId,
    selectedSuborganizationId,
    selectedOrganization,
    selectedSuborganization,
    load,
    select,
  }
})
