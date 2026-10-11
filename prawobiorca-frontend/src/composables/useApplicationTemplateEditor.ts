import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import { downloadApplicationTemplate } from '@/api/applicationTemplates'
import {
  publishApplicationTemplate,
  unpublishApplicationTemplate,
  updateApplicationTemplate,
} from '@/api/generated/endpoints/application-templates/application-templates'
import {
  toDetailsData,
  toEditableField,
  type ApplicationTemplateForm,
} from '@/domain/applicationTemplates'
import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

export function useApplicationTemplateEditor(
  onUpdated: (template: ApplicationTemplateRepresentation) => void,
) {
  const form = reactive<ApplicationTemplateForm>({
    name: '',
    instructions: '',
    organizationId: '',
    suborganizationId: '',
    fields: [],
  })
  const isSaving = ref(false)
  const isPublishing = ref(false)
  const isDownloading = ref(false)

  function resetForm(template: ApplicationTemplateRepresentation) {
    form.name = template.name
    form.instructions = template.instructions ?? ''
    form.organizationId = template.organizationId ?? ''
    form.suborganizationId = template.suborganizationId ?? ''
    form.fields = template.fields.map(toEditableField)
  }

  async function update(templateId: string): Promise<boolean> {
    try {
      onUpdated(await updateApplicationTemplate(templateId, toDetailsData(form)))
      return true
    } catch (error) {
      showApiError(error, {
        defaultMessage:
          'Nie udało się zapisać szablonu. Sprawdź nazwę, regexy, opcje list i wartości domyślne.',
      })
      return false
    }
  }

  async function save(templateId: string) {
    isSaving.value = true
    try {
      if (await update(templateId)) {
        ElMessage.success('Szablon został zapisany.')
      }
    } finally {
      isSaving.value = false
    }
  }

  async function publish(templateId: string) {
    isPublishing.value = true
    try {
      if (!(await update(templateId))) {
        return
      }
      onUpdated(await publishApplicationTemplate(templateId))
      ElMessage.success('Szablon został opublikowany.')
    } catch (error) {
      showApiError(error, {
        conflictMessage: 'Uzupełnij instrukcje dla AI przed publikacją.',
        defaultMessage: 'Nie udało się opublikować szablonu.',
      })
    } finally {
      isPublishing.value = false
    }
  }

  async function unpublish(templateId: string) {
    isPublishing.value = true
    try {
      onUpdated(await unpublishApplicationTemplate(templateId))
      ElMessage.success('Publikacja szablonu została wycofana.')
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się wycofać publikacji szablonu.' })
    } finally {
      isPublishing.value = false
    }
  }

  async function download(templateId: string) {
    isDownloading.value = true
    try {
      await downloadApplicationTemplate(templateId)
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonu.' })
    } finally {
      isDownloading.value = false
    }
  }

  return {
    form,
    isSaving,
    isPublishing,
    isDownloading,
    resetForm,
    save,
    publish,
    unpublish,
    download,
  }
}
