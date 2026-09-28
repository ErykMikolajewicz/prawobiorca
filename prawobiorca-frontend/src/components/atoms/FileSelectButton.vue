<script setup lang="ts">
import { ref } from 'vue'

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

function handleFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  selectedFile.value = input.files?.[0] ?? null
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
  margin-left: 12px;
  color: var(--el-text-color-secondary);
}
</style>
