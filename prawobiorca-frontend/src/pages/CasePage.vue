<script setup lang="ts">
import { computed, ref, onBeforeMount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'
import GeneratedApplicationsList from '@/components/organisms/GeneratedApplicationsList.vue'

import { useRegulationsPolling } from '@/composables/useRegulationsPolling'
import { useOrganizationsStore } from '@/stores/organizations'

import { downloadApplicationDocument } from '@/api/cases'
import {
  deleteApplication,
  deleteCaseDocument,
  generateApplication,
  getCaseApplications,
  getCaseDocuments,
} from '@/api/generated/endpoints/cases/cases'
import { getPublishedApplicationTemplates } from '@/api/generated/endpoints/application-templates/application-templates'

import type {
  ApplicationRepresentation,
  CaseDocument,
  NewApplication,
  PublishedApplicationTemplate,
} from '@/api/generated/model'

const route = useRoute()
const caseId = route.params.id as string
const organizationsStore = useOrganizationsStore()
let lastTemplatesRequestId = 0

const documents = ref<Array<CaseDocument>>([])
const applications = ref<Array<ApplicationRepresentation>>([])
const templates = ref<Array<PublishedApplicationTemplate>>([])
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

async function loadTemplates() {
  const requestId = ++lastTemplatesRequestId
  try {
    const fetchedTemplates = await getPublishedApplicationTemplates({
      organizationId: organizationsStore.selectedOrganizationId || undefined,
      suborganizationId: organizationsStore.selectedSuborganizationId || undefined,
    })
    if (requestId === lastTemplatesRequestId) {
      templates.value = fetchedTemplates
    }
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonów wniosków.' })
    templates.value = []
  }
}

watch(
  () => [organizationsStore.selectedOrganizationId, organizationsStore.selectedSuborganizationId],
  loadTemplates,
)

async function refreshApplications() {
  try {
    applications.value = await getCaseApplications(caseId)
  } catch (error) {
    console.error('Failed to refresh applications:', error)
  }
}

useRegulationsPolling(() => pendingApplicationIds.value, refreshApplications)

onBeforeMount(async () => {
  await Promise.all([loadDocuments(), loadApplications(), loadTemplates()])
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
    <div class="page-header">
      <h1 class="page-title">Szczegóły Sprawy</h1>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" :xs="24">
        <section class="case-section">
          <h2 class="section-title">Kontekst / Opis Wniosku</h2>
          <GeneratePdfForm :templates="templates" @generate-pdf="handleGeneratePdf" />
        </section>
      </el-col>
      <el-col :span="12" :xs="24">
        <section class="case-section">
          <h2 class="section-title">Przypięte Artykuły</h2>
          <PinnedDocumentsList :documents="documents" @unpin="handleUnpin" />
        </section>
        <section class="case-section">
          <h2 class="section-title">Wygenerowane Wnioski</h2>
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

<style scoped>
.case-section {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  margin-bottom: var(--app-space-xl);
}
</style>
