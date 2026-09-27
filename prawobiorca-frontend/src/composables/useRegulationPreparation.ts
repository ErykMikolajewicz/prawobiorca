import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getApiErrorMessage } from '@/utils/error'
import type { regulationPreparationStatus } from '@/types/api/regulations.ts'

export type preparationStatusOption = {
  label: string
  tagType: 'info' | 'warning' | 'danger'
}

export const preparationStatusOptions: Record<
  Exclude<regulationPreparationStatus, 'PREPARED'>,
  preparationStatusOption
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
      ElMessage.error(
        getApiErrorMessage(error, {
          conflictMessage: 'Regulacja jest już przetwarzana lub przygotowana.',
        }),
      )
      console.error('Nie udało się ponowić przetwarzania regulacji', error)
      return false
    } finally {
      isRetrying.value = false
    }
  }

  return { isRetrying, retry }
}
