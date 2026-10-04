<script setup lang="ts">
import { computed, ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import BackToMainButton from '@/components/atoms/BackToMainButton.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'
import GeneratedApplicationsList from '@/components/organisms/GeneratedApplicationsList.vue'

import { useRegulationsPolling } from '@/composables/useRegulationsPolling'

import { downloadApplicationDocument } from '@/api/cases'
import {
  deleteApplication,
  deleteCaseDocument,
  generateApplication,
  getCaseApplications,
  getCaseDocuments,
} from '@/api/generated/endpoints/cases/cases'

import type { ApplicationRepresentation, CaseDocument, NewApplication } from '@/api/generated/model'

const route = useRoute()
const caseId = route.params.id as string

const documents = ref<Array<CaseDocument>>([])
const applications = ref<Array<ApplicationRepresentation>>([])
const pendingApplicationIds = computed(() =>
  applications.value
    .filter((application) => application.generationStatus === 'IN_PROGRESS')
    .map((application) => application.id),
)

async function loadDocuments() {
  try {
    documents.value = await getCaseDocuments(caseId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać przypiętych dokumentów.' })
    documents.value = []
  }
}

async function loadApplications() {
  try {
    applications.value = await getCaseApplications(caseId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać wygenerowanych wniosków.' })
    applications.value = []
  }
}

async function refreshApplications() {
  try {
    applications.value = await getCaseApplications(caseId)
  } catch (error) {
    console.error('Failed to refresh applications:', error)
  }
}

useRegulationsPolling(() => pendingApplicationIds.value, refreshApplications)

onBeforeMount(async () => {
  await Promise.all([loadDocuments(), loadApplications()])
})

async function handleUnpin(documentId: string) {
  try {
    await deleteCaseDocument(documentId)
    documents.value = documents.value.filter((document) => document.id !== documentId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się odpiąć dokumentu.' })
  }
}

const handleGeneratePdf = async (newApplication: NewApplication) => {
  try {
    await generateApplication(caseId, newApplication)
    ElMessage({
      message: 'Wniosek jest generowany. Pobierzesz go z listy, gdy będzie gotowy.',
      type: 'success',
      duration: 5000,
    })
    await loadApplications()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się zlecić wygenerowania wniosku.' })
  }
}

async function handleDownloadApplication(applicationId: string) {
  try {
    await downloadApplicationDocument(applicationId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać wniosku.' })
  }
}

async function handleDeleteApplication(applicationId: string) {
  try {
    await deleteApplication(applicationId)
    applications.value = applications.value.filter(
      (application) => application.id !== applicationId,
    )
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć wniosku.' })
  }
}
</script>

<template>
  <AppLayout>
    <BackToMainButton />

    <h1>Szczegóły Sprawy</h1>

    <el-row :gutter="20">
      <el-col :span="12" :xs="24">
        <section>
          <h2>Kontekst / Opis Wniosku</h2>
          <GeneratePdfForm @generate-pdf="handleGeneratePdf" />
        </section>
      </el-col>
      <el-col :span="12" :xs="24">
        <section>
          <h2>Przypięte Artykuły</h2>
          <PinnedDocumentsList :documents="documents" @unpin="handleUnpin" />
        </section>
        <section>
          <h2>Wygenerowane Wnioski</h2>
          <GeneratedApplicationsList
            :applications="applications"
            @download="handleDownloadApplication"
            @delete="handleDeleteApplication"
          />
        </section>
      </el-col>
    </el-row>
  </AppLayout>
</template>
