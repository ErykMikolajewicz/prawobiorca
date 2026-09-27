<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

import AppNavbar from '@/components/organisms/AppNavbar.vue'
import AppFooter from '@/components/organisms/AppFooter.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'

import { generatePdf } from '@/api/cases.ts'
import { deleteCaseDocument, getCaseDocuments } from '@/api/generated/endpoints/cases/cases'

import type { DocumentData } from '@/types/api/documents.ts'
import { ArrowLeft } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const caseId = route.params.id as string

const authStore = useAuthStore()
const { isUserLogged } = storeToRefs(authStore)

const documents = ref<Array<DocumentData>>([])

const loadDocuments = async () => {
  if (isUserLogged.value) {
    try {
      documents.value = await getCaseDocuments(caseId)
    } catch (error) {
      console.error('Failed to fetch case articles:', error)
      documents.value = []
    }
  }
}

onBeforeMount(async () => {
  await loadDocuments()
})

const handleUnpin = async (articleId: string) => {
  await deleteCaseDocument(articleId)
  await loadDocuments()
}

const handleGeneratePdf = async (description: string) => {
  await generatePdf(caseId, description)
}
</script>

<template>
  <div class="page-container">
    <AppNavbar />

    <main class="case-page">
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
            <GeneratePdfForm :case-id="caseId" @generate-pdf="handleGeneratePdf" />
          </section>
        </el-col>
      </el-row>
    </main>

    <AppFooter />
  </div>
</template>

<style scoped>
.page-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.case-page {
  flex-grow: 1;
  padding: 1rem;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .case-page {
    padding: 0.5rem;
  }
}
</style>
