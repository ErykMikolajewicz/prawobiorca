import { ref } from 'vue'
import { showApiError } from '@/utils/error'
import { deleteCaseDocument, getCaseDocuments } from '@/api/generated/endpoints/cases/cases'
import type { CaseDocument } from '@/api/generated/model'

export function useCaseDocuments(caseId: string) {
  const documents = ref<Array<CaseDocument>>([])

  async function load() {
    try {
      documents.value = await getCaseDocuments(caseId)
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać przypiętych dokumentów.' })
      documents.value = []
    }
  }

  async function unpin(documentId: string) {
    try {
      await deleteCaseDocument(caseId, documentId)
      documents.value = documents.value.filter((document) => document.id !== documentId)
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się odpiąć dokumentu.' })
    }
  }

  return {
    documents,
    load,
    unpin,
  }
}
