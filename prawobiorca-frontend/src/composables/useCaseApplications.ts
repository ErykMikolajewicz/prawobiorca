import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'
import { useRegulationsPolling } from '@/composables/useRegulationsPolling'
import { downloadApplicationDocument } from '@/api/cases'
import {
  deleteApplication,
  generateApplication,
  getCaseApplications,
} from '@/api/generated/endpoints/cases/cases'
import type { ApplicationRepresentation, NewApplication } from '@/api/generated/model'

function isPending(application: ApplicationRepresentation): boolean {
  return application.generationStatus === 'IN_PROGRESS'
}

export function useCaseApplications(caseId: string) {
  const applications = ref<Array<ApplicationRepresentation>>([])
  const pendingIds = computed(() =>
    applications.value.filter(isPending).map((application) => application.id),
  )

  async function load() {
    try {
      applications.value = await getCaseApplications(caseId)
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać wygenerowanych wniosków.' })
      applications.value = []
    }
  }

  async function refresh() {
    try {
      applications.value = await getCaseApplications(caseId)
    } catch (error) {
      console.error('Failed to refresh applications:', error)
    }
  }

  async function generate(newApplication: NewApplication) {
    try {
      await generateApplication(caseId, newApplication)
      ElMessage({
        message: 'Wniosek jest generowany. Pobierzesz go z listy, gdy będzie gotowy.',
        type: 'success',
        duration: 5000,
      })
      await load()
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się zlecić wygenerowania wniosku.' })
    }
  }

  async function download(applicationId: string) {
    try {
      await downloadApplicationDocument(applicationId)
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się pobrać wniosku.' })
    }
  }

  async function remove(applicationId: string) {
    try {
      await deleteApplication(applicationId)
      applications.value = applications.value.filter(
        (application) => application.id !== applicationId,
      )
    } catch (error) {
      showApiError(error, { defaultMessage: 'Nie udało się usunąć wniosku.' })
    }
  }

  useRegulationsPolling(() => pendingIds.value, refresh)

  return {
    applications,
    load,
    generate,
    download,
    remove,
  }
}
