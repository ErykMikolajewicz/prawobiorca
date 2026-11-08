import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { getCasesList } from '@/api/generated/endpoints/cases/cases'
import type { CaseData } from '@/api/generated/model'
import { showApiError } from '@/utils/error'

const ACTIVE_CASE_STORAGE_KEY = 'active-case-id'

export const useCasesStore = defineStore('cases', () => {
  const cases = ref<Array<CaseData>>([])
  const activeCaseId = ref<string>('')
  const activeCase = computed(() => cases.value.find((c) => c.id === activeCaseId.value))

  function setActive(caseId: string): void {
    activeCaseId.value = caseId
    localStorage.setItem(ACTIVE_CASE_STORAGE_KEY, caseId)
  }

  async function load(): Promise<void> {
    try {
      cases.value = await getCasesList()
      const storedCaseId = localStorage.getItem(ACTIVE_CASE_STORAGE_KEY)
      const storedCase = cases.value.find((c) => c.id === storedCaseId)
      activeCaseId.value = storedCase?.id ?? cases.value[0]?.id ?? ''
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać spraw.' })
    }
  }

  function add(newCase: CaseData): void {
    cases.value.unshift(newCase)
    setActive(newCase.id)
  }

  function remove(caseId: string): void {
    cases.value = cases.value.filter((c) => c.id !== caseId)
    if (activeCaseId.value === caseId) {
      setActive(cases.value[0]?.id ?? '')
    }
  }

  return { cases, activeCaseId, activeCase, load, add, remove, setActive }
})
