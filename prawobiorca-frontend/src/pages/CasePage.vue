<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import BackToMainButton from '@/components/atoms/BackToMainButton.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'
import GeneratedApplicationsList from '@/components/organisms/GeneratedApplicationsList.vue'

import { downloadApplicationDocument, generateApplicationDocument } from '@/api/cases'
import {
  deleteApplication,
  deleteCaseDocument,
  getCaseApplications,
  getCaseDocuments,
} from '@/api/generated/endpoints/cases/cases'

import type { ApplicationRepresentation, CaseDocument, NewApplication } from '@/api/generated/model'

const route = useRoute()
const caseId = route.params.id as string

const documents = ref<Array<CaseDocument>>([])
const applications = ref<Array<ApplicationRepresentation>>([])

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
    await generateApplicationDocument(caseId, newApplication)
    ElMessage({
      message: 'Wniosek został pomyślnie wygenerowany.',
      type: 'success',
      duration: 5000,
    })
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się wygenerować wniosku.' })
  }
  await loadApplications()
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

    <el-row>
      <el-col :span="12" :xs="24">
        <section>
          <h2>Przypięte Dokumenty</h2>
          <PinnedDocumentsList :documents="documents" @unpin="handleUnpin" />
        </section>
      </el-col>
      <el-col :span="12" :xs="24">
        <section>
          <h2>Kontekst / Opis Wniosku</h2>
          <GeneratePdfForm @generate-pdf="handleGeneratePdf" />
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
