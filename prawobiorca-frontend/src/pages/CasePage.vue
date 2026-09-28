<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'

import { generatePdf } from '@/api/cases'
import { deleteCaseDocument, getCaseDocuments } from '@/api/generated/endpoints/cases/cases'

import type { CaseDocument } from '@/api/generated/model'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id as string

const authStore = useAuthStore()
const { isUserLogged } = storeToRefs(authStore)

const documents = ref<Array<CaseDocument>>([])

async function loadDocuments() {
  if (isUserLogged.value) {
    try {
      documents.value = await getCaseDocuments(caseId)
    } catch (error) {
      showApiError(error, { defaultServerMessage: 'Nie udało się pobrać przypiętych dokumentów.' })
      documents.value = []
    }
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
    showApiError(error, { defaultServerMessage: 'Nie udało się odpiąć dokumentu.' })
  }
}

const handleGeneratePdf = async (description: string) => {
  try {
    await generatePdf(caseId, description)
  } catch (error) {
    showApiError(error, { defaultServerMessage: 'Nie udało się wygenerować wniosku.' })
  }
}
</script>

<template>
  <AppLayout>
    <el-button link @click="router.push('/')">
      <el-icon><ArrowLeft /></el-icon> Powrót do głównego ekranu
    </el-button>

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
