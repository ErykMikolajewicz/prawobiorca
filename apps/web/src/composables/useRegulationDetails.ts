import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import {
  deleteRegulation,
  getRegulationDownloadUrlById,
  regenerateRegulationDescription,
  updateRegulation,
} from '@/api/generated/endpoints/regulations/regulations'
import { showApiError } from '@/utils/error'
import { toBrowserStorageUrl } from '@/utils/storage'
import type { RegulationRepresentation } from '@/api/generated/model'

export function useRegulationDetails() {
  const name = ref('')
  const description = ref('')
  const isSaving = ref(false)
  const isDeleting = ref(false)
  const isLoadingPreview = ref(false)
  const isGeneratingDescription = ref(false)

  function resetForm(regulation: RegulationRepresentation) {
    name.value = regulation.presentationName
    description.value = regulation.description ?? ''
  }

  async function save(regulationId: string): Promise<RegulationRepresentation | null> {
    if (!name.value.trim()) {
      ElMessage.warning('Podaj nazwę regulacji.')
      return null
    }

    try {
      isSaving.value = true
      const regulation = await updateRegulation(regulationId, {
        name: name.value.trim(),
        description: description.value.trim() || null,
      })
      ElMessage.success('Regulacja została zaktualizowana')
      return regulation
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się zaktualizować regulacji' })
      return null
    } finally {
      isSaving.value = false
    }
  }

  async function remove(regulationId: string): Promise<boolean> {
    try {
      isDeleting.value = true
      await deleteRegulation(regulationId)
      ElMessage.success('Regulacja została usunięta')
      return true
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się usunąć regulacji' })
      return false
    } finally {
      isDeleting.value = false
    }
  }

  async function generateDescription(regulationId: string): Promise<boolean> {
    try {
      isGeneratingDescription.value = true
      await regenerateRegulationDescription(regulationId)
      ElMessage.success('Generowanie opisu zostało rozpoczęte')
      return true
    } catch (error) {
      showApiError(error, {
        defaultMessage: 'Nie udało się rozpocząć generowania opisu',
        conflictMessage: 'Opis jest już generowany lub regulacja nie jest jeszcze przetworzona.',
      })
      return false
    } finally {
      isGeneratingDescription.value = false
    }
  }

  async function showPreview(regulationId: string) {
    const previewWindow = window.open('', '_blank')
    try {
      isLoadingPreview.value = true
      const previewUrl = toBrowserStorageUrl(await getRegulationDownloadUrlById(regulationId))
      if (previewWindow) {
        previewWindow.opener = null
        previewWindow.location.href = previewUrl
      }
    } catch (error) {
      previewWindow?.close()
      showApiError(error, { defaultMessage: 'Nie udało się pobrać podglądu pliku' })
    } finally {
      isLoadingPreview.value = false
    }
  }

  return {
    name,
    description,
    isSaving,
    isDeleting,
    isLoadingPreview,
    isGeneratingDescription,
    resetForm,
    save,
    remove,
    generateDescription,
    showPreview,
  }
}
