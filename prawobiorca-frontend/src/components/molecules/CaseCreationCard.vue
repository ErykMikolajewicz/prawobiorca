<script setup lang="ts">
import { ref } from 'vue'
import Add2RoundedIcon from '@iconify-vue/material-symbols/add-2-rounded'
import type { InputInstance } from 'element-plus'
import { addCase } from '@/api/generated/endpoints/cases/cases'
import { showApiError } from '@/utils/error'
import type { CaseData } from '@/api/generated/model'

const newCaseName = ref('')
const isCreating = ref(false)
const inputRef = ref<InputInstance>()

const emit = defineEmits<{
  (e: 'case-created', newCase: CaseData): void
}>()

async function createCase() {
  if (newCaseName.value.trim() === '' || isCreating.value) {
    return
  }

  isCreating.value = true
  try {
    const caseId: string = await addCase({ caseName: newCaseName.value.trim() })
    const newCase: CaseData = {
      id: caseId,
      name: newCaseName.value.trim(),
    }
    emit('case-created', newCase)
    newCaseName.value = ''
  } catch (error) {
    showApiError(error, { defaultMessage: 'Nie udało się utworzyć sprawy.' })
  } finally {
    isCreating.value = false
  }
}
</script>

<template>
  <el-card shadow="never" class="form-card" @click="inputRef?.focus()">
    <form class="case-form" @submit.prevent="createCase">
      <el-input
        id="case_name"
        ref="inputRef"
        v-model="newCaseName"
        name="case_name"
        placeholder="Utwórz nową sprawę..."
        required
        class="case-name-input"
      />
      <button type="submit" class="icon-btn" aria-label="Utwórz sprawę" :disabled="isCreating">
        <Add2RoundedIcon />
      </button>
    </form>
  </el-card>
</template>

<style scoped>
.form-card {
  border: dashed 2px var(--el-color-primary-light-8);
  background-color: var(--el-color-primary-light-9);
  cursor: text;

  &:hover {
    background-color: var(--el-color-primary-light-7);
    border-color: var(--el-color-primary-light-5);
  }

  form {
    display: flex;
  }
}

.case-name-input {
  font-size: 1.1em;

  :deep(.el-input__wrapper) {
    padding: 0;
    background: transparent;
    box-shadow: none;
  }
}
</style>
