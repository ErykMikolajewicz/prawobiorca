<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

type Props = {
  label?: string
}

withDefaults(defineProps<Props>(), {
  label: 'Wybierz plik',
})

const selectedFile = defineModel<File | null>({ required: true })

const fileInputRef = ref<HTMLInputElement | null>(null)

function triggerFileInput() {
  fileInputRef.value?.click()
}

async function copyToMemory(file: File): Promise<File> {
  return new File([await file.arrayBuffer()], file.name, {
    type: file.type,
    lastModified: file.lastModified,
  })
}

async function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0] ?? null
  input.value = ''

  if (!file) {
    selectedFile.value = null
    return
  }

  try {
    selectedFile.value = await copyToMemory(file)
  } catch (error) {
    selectedFile.value = null
    ElMessage.error('Nie udało się odczytać pliku. Wybierz go ponownie.')
    console.error(error)
  }
}
</script>

<template>
  <span class="file-select">
    <input ref="fileInputRef" type="file" class="hidden-file-input" @change="handleFileChange" />
    <el-button @click="triggerFileInput">{{ label }}</el-button>
    <span v-if="selectedFile" class="selected-file-name">{{ selectedFile.name }}</span>
  </span>
</template>

<style scoped>
.file-select {
  display: inline-flex;
  align-items: center;
}

.hidden-file-input {
  display: none;
}

.selected-file-name {
  margin-left: var(--app-space-md);
  color: var(--el-text-color-secondary);
}
</style>
