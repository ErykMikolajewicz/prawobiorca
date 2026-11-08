<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import axios from 'axios'
import { getAdminApplicationTemplateDownloadUrl } from '@/api/generated/endpoints/application-templates/application-templates'
import { showApiError } from '@/utils/error'
import { toBrowserStorageUrl } from '@/utils/storage'

type Props = {
  templateId: string
}

const props = defineProps<Props>()

const visible = defineModel<boolean>({ required: true })

const previewContainer = ref<HTMLDivElement | null>(null)
const isLoading = ref(false)

watch(visible, async (isVisible) => {
  if (isVisible) {
    await nextTick()
    await loadPreview()
  }
})

async function loadPreview() {
  if (!previewContainer.value) {
    return
  }
  isLoading.value = true
  try {
    const url = toBrowserStorageUrl(await getAdminApplicationTemplateDownloadUrl(props.templateId))
    const response = await axios.get<Blob>(url, { responseType: 'blob' })
    const { renderAsync } = await import('docx-preview')
    await renderAsync(response.data, previewContainer.value)
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się wczytać podglądu szablonu.' })
  } finally {
    isLoading.value = false
  }
}

function clearPreview() {
  previewContainer.value?.replaceChildren()
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="Podgląd szablonu"
    width="min(900px, 92vw)"
    append-to-body
    @closed="clearPreview"
  >
    <div ref="previewContainer" v-loading="isLoading" class="preview-container" />
  </el-dialog>
</template>

<style scoped>
.preview-container {
  min-height: 200px;
  max-height: 75vh;
  overflow: auto;
}
</style>
