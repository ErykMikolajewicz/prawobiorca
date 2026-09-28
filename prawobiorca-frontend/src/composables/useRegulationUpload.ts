import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import {
  addPublicRegulation,
  confirmPublicRegulationUpload,
} from '@/api/generated/endpoints/regulations/regulations'
import {
  addUserRegulation,
  confirmUserRegulationUpload,
} from '@/api/generated/endpoints/user-regulations/user-regulations'
import { uploadFileToStorage } from '@/utils/storage'
import type { RegulationScope } from '@/domain/regulations'
import type {
  RegulationPreparationStatus,
  RegulationRepresentation,
  RegulationType,
} from '@/api/generated/model'

type RegulationUploadResult = {
  id: string
  preparationStatus: RegulationPreparationStatus
}

async function confirmUpload(
  regulationId: string,
  confirm: (regulationId: string) => Promise<unknown>,
): Promise<RegulationUploadResult> {
  try {
    await confirm(regulationId)
    return { id: regulationId, preparationStatus: 'IN_PROGRESS' }
  } catch (error) {
    console.error('Failed to confirm regulation upload:', error)
    return { id: regulationId, preparationStatus: 'NOT_STARTED' }
  }
}

async function uploadRegulation(
  target: RegulationScope,
  regulation: File,
  presentationName: string,
  regulationType?: RegulationType,
): Promise<RegulationUploadResult> {
  const addRegulation = target === 'public' ? addPublicRegulation : addUserRegulation
  const confirm = target === 'public' ? confirmPublicRegulationUpload : confirmUserRegulationUpload

  const uploadTarget = await addRegulation({
    name: presentationName,
    regulationType: regulationType || null,
  })

  await uploadFileToStorage(uploadTarget, regulation)

  return await confirmUpload(uploadTarget.id, confirm)
}

export function useRegulationUpload() {
  const selectedFile = ref<File | null>(null)
  const presentationName = ref('')
  const selectedRegulationType = ref<RegulationType | ''>('')
  const target = ref<RegulationScope>('user')
  const isSubmitting = ref(false)

  function resetForm() {
    selectedFile.value = null
    presentationName.value = ''
    selectedRegulationType.value = ''
    target.value = 'user'
  }

  function setFile(file: File | null) {
    selectedFile.value = file
    if (file) {
      presentationName.value = file.name
    }
  }

  async function submit(): Promise<{
    regulation: RegulationRepresentation
    target: RegulationScope
  } | null> {
    if (!selectedFile.value) {
      ElMessage.warning('Wybierz plik do przesłania.')
      return null
    }

    if (!presentationName.value.trim()) {
      ElMessage.warning('Podaj nazwę pliku.')
      return null
    }

    isSubmitting.value = true
    try {
      const regulationTypeValue = selectedRegulationType.value || undefined
      const uploadResult = await uploadRegulation(
        target.value,
        selectedFile.value,
        presentationName.value.trim(),
        regulationTypeValue,
      )

      if (uploadResult.preparationStatus === 'IN_PROGRESS') {
        ElMessage.success('Plik został dodany i jest przetwarzany.')
      } else {
        ElMessage.warning('Plik został wgrany, ale nie udało się rozpocząć przetwarzania.')
      }

      return {
        regulation: {
          id: uploadResult.id,
          presentationName: presentationName.value.trim(),
          regulationType: regulationTypeValue ?? null,
          preparationStatus: uploadResult.preparationStatus,
        },
        target: target.value,
      }
    } catch (error) {
      showApiError(error, { defaultMessage: 'Wystąpił błąd podczas dodawania pliku.' })
      return null
    } finally {
      isSubmitting.value = false
    }
  }

  return {
    selectedFile,
    presentationName,
    selectedRegulationType,
    target,
    isSubmitting,
    resetForm,
    setFile,
    submit,
  }
}
