<script setup lang="ts">
import { onBeforeMount, reactive } from 'vue'
import { useRoute } from 'vue-router'

import AppLayout from '@/components/templates/AppLayout.vue'
import PinnedDocumentsList from '@/components/organisms/PinnedDocumentsList.vue'
import GeneratePdfForm from '@/components/organisms/GeneratePdfForm.vue'
import GeneratedApplicationsList from '@/components/organisms/GeneratedApplicationsList.vue'

import { useCaseDocuments } from '@/composables/useCaseDocuments'
import { useCaseApplications } from '@/composables/useCaseApplications'
import { usePublishedTemplates } from '@/composables/usePublishedTemplates'

const route = useRoute()
const caseId = route.params.id as string

const caseDocuments = reactive(useCaseDocuments(caseId))
const caseApplications = reactive(useCaseApplications(caseId))
const publishedTemplates = reactive(usePublishedTemplates())

onBeforeMount(async () => {
  await Promise.all([caseDocuments.load(), caseApplications.load(), publishedTemplates.load()])
})
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
          <GeneratePdfForm
            :templates="publishedTemplates.templates"
            :scores="publishedTemplates.scores"
            :searching="publishedTemplates.searching"
            @generate-pdf="caseApplications.generate"
            @search="publishedTemplates.search"
          />
        </section>
      </el-col>
      <el-col :span="12" :xs="24">
        <section class="case-section">
          <h2 class="section-title">Przypięte Artykuły</h2>
          <PinnedDocumentsList :documents="caseDocuments.documents" @unpin="caseDocuments.unpin" />
        </section>
        <section class="case-section">
          <h2 class="section-title">Wygenerowane Wnioski</h2>
          <GeneratedApplicationsList
            :applications="caseApplications.applications"
            @download="caseApplications.download"
            @delete="caseApplications.remove"
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
