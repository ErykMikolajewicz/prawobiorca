<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import ApplicationTemplatesList from '@/components/organisms/ApplicationTemplatesList.vue'
import ApplicationTemplateUploadDialog from '@/components/molecules/ApplicationTemplateUploadDialog.vue'

import {
  deleteApplicationTemplate,
  getApplicationTemplates,
} from '@/api/generated/endpoints/application-templates/application-templates'

import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

const router = useRouter()

const templates = ref<Array<ApplicationTemplateRepresentation>>([])
const isLoading = ref(false)
const isUploadDialogVisible = ref(false)

async function loadTemplates() {
  isLoading.value = true
  try {
    templates.value = await getApplicationTemplates()
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonów wniosków.' })
  } finally {
    isLoading.value = false
  }
}

async function openTemplate(templateId: string) {
  await router.push({ name: 'ApplicationTemplatePage', params: { id: templateId } })
}

async function handleDelete(templateId: string) {
  try {
    await deleteApplicationTemplate(templateId)
    templates.value = templates.value.filter((template) => template.id !== templateId)
    ElMessage.success('Szablon został usunięty.')
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się usunąć szablonu.' })
  }
}

onBeforeMount(loadTemplates)
</script>

<template>
  <AppLayout>
    <div class="page-header">
      <h1>Szablony wniosków</h1>
      <el-button type="primary" @click="isUploadDialogVisible = true">Dodaj szablon</el-button>
    </div>

    <ApplicationTemplatesList
      :templates="templates"
      :loading="isLoading"
      @select="openTemplate"
      @delete="handleDelete"
    />

    <ApplicationTemplateUploadDialog v-model="isUploadDialogVisible" @submitted="openTemplate" />
  </AppLayout>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}
</style>
