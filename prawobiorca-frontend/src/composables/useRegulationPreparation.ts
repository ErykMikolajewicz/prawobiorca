import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

export function useRegulationPreparation(
  retryFn: (regulationId: string) => Promise<unknown>,
  conflictMessage = 'Regulacja jest już przetwarzana lub przygotowana.',
) {
  const isRetrying = ref(false)

  async function retry(regulationId: string): Promise<boolean> {
    isRetrying.value = true
    try {
      await retryFn(regulationId)
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
