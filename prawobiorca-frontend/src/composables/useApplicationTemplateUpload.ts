import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import {
  addApplicationTemplate,
  confirmApplicationTemplateUpload,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { uploadFileToStorage } from '@/utils/storage'

export function useApplicationTemplateUpload() {
  const selectedFile = ref<File | null>(null)
  const name = ref('')
  const isSubmitting = ref(false)

  function resetForm() {
    selectedFile.value = null
    name.value = ''
  }

  function setFile(file: File | null) {
    selectedFile.value = file
    if (file) {
      name.value = file.name.replace(/\.docx$/i, '')
    }
  }

  async function submit(): Promise<string | null> {
    if (!selectedFile.value) {
      ElMessage.warning('Wybierz plik szablonu.')
      return null
    }

    if (!name.value.trim()) {
      ElMessage.warning('Podaj nazwę szablonu.')
      return null
    }

    isSubmitting.value = true
    let templateId: string | null = null
    try {
      const uploadTarget = await addApplicationTemplate({ name: name.value.trim() })
      templateId = uploadTarget.id

      await uploadFileToStorage(uploadTarget, selectedFile.value)
      await confirmApplicationTemplateUpload(templateId)

      ElMessage.success('Szablon został dodany. Skonfiguruj pola i instrukcje dla AI.')
    } catch (error) {
      showApiError(error, {
        defaultMessage:
          'Nie udało się wczytać szablonu. Sprawdź, czy to plik DOCX zawierający zmienną paragraphs.',
      })
    } finally {
      isSubmitting.value = false
    }

    return templateId
  }

  return {
    selectedFile,
    name,
    isSubmitting,
    resetForm,
    setFile,
    submit,
  }
}
