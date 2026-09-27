import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import type { RegulationPreparationStatus } from '@/api/generated/model'

export type PreparationStatusOption = {
  label: string
  tagType: 'info' | 'warning' | 'danger'
}

export const preparationStatusOptions: Record<
  Exclude<RegulationPreparationStatus, 'PREPARED'>,
  PreparationStatusOption
> = {
  NOT_STARTED: { label: 'Oczekuje', tagType: 'info' },
  IN_PROGRESS: { label: 'Przetwarzanie', tagType: 'warning' },
  FAILED: { label: 'Błąd przetwarzania', tagType: 'danger' },
}

export function useRegulationPreparation(retryFn: (regulationId: string) => Promise<unknown>) {
  const isRetrying = ref(false)

  async function retry(regulationId: string): Promise<boolean> {
    isRetrying.value = true
    try {
      await retryFn(regulationId)
      ElMessage.success('Ponowne przetwarzanie zostało rozpoczęte')
      return true
    } catch (error) {
      showApiError(error, {
        conflictMessage: 'Regulacja jest już przetwarzana lub przygotowana.',
      })
      return false
    } finally {
      isRetrying.value = false
    }
  }

  return { isRetrying, retry }
}
