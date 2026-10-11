import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  confirmPublicRegulationUpload,
  retryPublicRegulationPreparation,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  confirmUserRegulationUpload,
  retryUserRegulationPreparation,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { showApiError } from '@/utils/error'
import type { RegulationRepresentation } from '@/api/generated/model'
import type { RegulationScope } from '@/domain/regulations'

export function useRegulationPreparation(target: RegulationScope) {
  const isRetrying = ref(false)

  const retryRegulationPreparation =
    target === 'public' ? retryPublicRegulationPreparation : retryUserRegulationPreparation
  const confirmRegulationUpload =
    target === 'public' ? confirmPublicRegulationUpload : confirmUserRegulationUpload

  async function retry(regulation: RegulationRepresentation): Promise<boolean> {
    const isNotStarted = regulation.preparationStatus === 'NOT_STARTED'
    const retryFn = isNotStarted ? confirmRegulationUpload : retryRegulationPreparation
    const conflictMessage = isNotStarted
      ? 'Pliku nie ma w magazynie. Usuń regulację i dodaj ją ponownie.'
      : 'Regulacja jest już przetwarzana lub przygotowana.'

    isRetrying.value = true
    try {
      await retryFn(regulation.id)
      ElMessage.success('Ponowne przetwarzanie zostało rozpoczęte')
      return true
    } catch (error) {
      showApiError(error, { conflictMessage })
      return false
    } finally {
      isRetrying.value = false
    }
  }

  return { isRetrying, retry }
}
