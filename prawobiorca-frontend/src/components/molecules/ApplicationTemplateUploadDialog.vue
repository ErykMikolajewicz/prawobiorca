<script setup lang="ts">
import { watch } from 'vue'
import FileSelectButton from '@/components/atoms/FileSelectButton.vue'
import { useApplicationTemplateUpload } from '@/composables/useApplicationTemplateUpload'

const visible = defineModel<boolean>({ required: true })

const emit = defineEmits<{
  (e: 'submitted', templateId: string): void
}>()

const { selectedFile, name, isSubmitting, resetForm, setFile, submit } =
  useApplicationTemplateUpload()

watch(visible, (isVisible) => {
  if (isVisible) {
    resetForm()
  }
})

function closeDialog() {
  visible.value = false
}

async function handleSubmit() {
  const templateId = await submit()
  if (!templateId) {
    return
  }

  emit('submitted', templateId)
  closeDialog()
}
</script>

<template>
  <el-dialog v-model="visible" title="Dodaj szablon wniosku" width="min(480px, 92vw)">
    <el-form label-position="top" @submit.prevent="handleSubmit">
      <el-form-item label="Plik DOCX:">
        <FileSelectButton :model-value="selectedFile" @update:model-value="setFile" />
      </el-form-item>

      <el-form-item label="Nazwa szablonu:">
        <el-input v-model="name" placeholder="Nazwa szablonu" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="closeDialog">Anuluj</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleSubmit">Dodaj</el-button>
    </template>
  </el-dialog>
</template>
