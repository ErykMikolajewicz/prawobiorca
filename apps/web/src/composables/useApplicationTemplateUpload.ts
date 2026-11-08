import axios from 'axios'
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import {
  addApplicationTemplate,
  confirmApplicationTemplateUpload,
} from '@/api/generated/endpoints/application-templates/application-templates'
import { uploadFileToStorage } from '@/utils/storage'
import type { ApplicationTemplateUploadTarget } from '@/api/generated/model'

async function sendTemplateFile(
  uploadTarget: ApplicationTemplateUploadTarget,
  file: File,
  signal: AbortSignal,
): Promise<boolean> {
  try {
    await uploadFileToStorage(uploadTarget, file, signal)
    return true
  } catch (error) {
    if (!axios.isCancel(error)) {
      ElMessage.error('Nie udało się wysłać pliku szablonu. Spróbuj ponownie.')
      console.error(error)
    }
    return false
  }
}

export function useApplicationTemplateUpload() {
  const selectedFile = ref<File | null>(null)
  const name = ref('')
  const isSubmitting = ref(false)
  let abortController: AbortController | null = null

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

  function cancelSubmit() {
    abortController?.abort()
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
    abortController = new AbortController()
    const { signal } = abortController
    let templateId: string | null = null
    try {
      const uploadTarget = await addApplicationTemplate({ name: name.value.trim() }, { signal })

      const isFileSent = await sendTemplateFile(uploadTarget, selectedFile.value, signal)
      if (!isFileSent) {
        return null
      }

      templateId = uploadTarget.id
      await confirmApplicationTemplateUpload(templateId, { signal })

      ElMessage.success('Szablon został dodany. Skonfiguruj pola i instrukcje dla AI.')
    } catch (error) {
      if (axios.isCancel(error)) {
        return null
      }

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
    cancelSubmit,
    submit,
  }
}
