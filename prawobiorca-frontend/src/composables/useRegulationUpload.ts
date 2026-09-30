import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { uploadUserRegulation, uploadPublicRegulation } from '@/api/regulations'
import type { regulationRepresentation, regulationType } from '@/types/api/regulations.ts'

export type uploadTarget = 'user' | 'public'

export const regulationTypeOptions: Array<{ label: string; value: regulationType }> = [
  { label: 'Ustawa', value: 'ACT' },
  { label: 'Rozporządzenie', value: 'DECREE' },
  { label: 'Regulamin', value: 'STATUTE' },
]

export function useRegulationUpload() {
  const selectedFile = ref<File | null>(null)
  const presentationName = ref('')
  const selectedRegulationType = ref<regulationType | ''>('')
  const target = ref<uploadTarget>('user')
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
    regulation: regulationRepresentation
    target: uploadTarget
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
      const uploadFn = target.value === 'public' ? uploadPublicRegulation : uploadUserRegulation

      const uploadResult = await uploadFn(
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
    } catch {
      ElMessage.error('Wystąpił błąd podczas dodawania pliku.')
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
