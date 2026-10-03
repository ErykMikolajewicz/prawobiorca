<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import BackToMainButton from '@/components/atoms/BackToMainButton.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'

import { generatePdf } from '@/api/cases'
import { deleteCaseDocument, getCaseDocuments } from '@/api/generated/endpoints/cases/cases'

import type { CaseDocument, NewApplication } from '@/api/generated/model'

const route = useRoute()
const caseId = route.params.id as string

const documents = ref<Array<CaseDocument>>([])

async function loadDocuments() {
  try {
    documents.value = await getCaseDocuments(caseId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać przypiętych dokumentów.' })
    documents.value = []
  }
}

onBeforeMount(async () => {
  await loadDocuments()
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
    await generatePdf(caseId, newApplication)
    ElMessage({
      message: 'Wniosek został pomyślnie wygenerowany.',
      type: 'success',
      duration: 5000,
    })
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się wygenerować wniosku.' })
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
      </el-col>
    </el-row>
  </AppLayout>
</template>
