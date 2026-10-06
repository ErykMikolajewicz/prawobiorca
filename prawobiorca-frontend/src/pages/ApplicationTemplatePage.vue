<script setup lang="ts">
import { ref, onBeforeMount } from 'vue'
import { useRoute } from 'vue-router'
import { showApiError } from '@/utils/error'

import AppLayout from '@/components/templates/AppLayout.vue'
import ApplicationTemplateEditor from '@/components/organisms/ApplicationTemplateEditor.vue'

import { getAdminApplicationTemplate } from '@/api/generated/endpoints/application-templates/application-templates'

import type { ApplicationTemplateRepresentation } from '@/api/generated/model'

const route = useRoute()
const templateId = route.params.id as string

const template = ref<ApplicationTemplateRepresentation | null>(null)
const isLoading = ref(false)

async function loadTemplate() {
  isLoading.value = true
  try {
    template.value = await getAdminApplicationTemplate(templateId)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się pobrać szablonu wniosku.' })
  } finally {
    isLoading.value = false
  }
}

onBeforeMount(loadTemplate)
</script>

<template>
  <AppLayout>
    <div v-loading="isLoading" class="template-page">
      <ApplicationTemplateEditor
        v-if="template"
        :template="template"
        @updated="(updatedTemplate) => (template = updatedTemplate)"
      />
      <el-empty v-else-if="!isLoading" description="Nie znaleziono szablonu." />
    </div>
  </AppLayout>
</template>

<style scoped>
.template-page {
  min-height: 120px;
}
</style>
