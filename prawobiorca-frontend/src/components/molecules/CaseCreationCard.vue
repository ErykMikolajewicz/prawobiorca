<script setup lang="ts">
import { ref } from 'vue'
import Add2RoundedIcon from '@iconify-vue/material-symbols/add-2-rounded'
import { ElMessage } from 'element-plus'
import { addCase } from '@/api/generated/endpoints/cases/cases'
import { getApiErrorMessage } from '@/utils/error'

const newCaseName = ref('')
const inputRef = ref<HTMLInputElement>()

const emit = defineEmits<{
  (e: 'case-created', newCase: { id: string; name: string }): void
}>()

async function createCase() {
  if (newCaseName.value.trim() === '') {
    return
  }

  try {
    const caseId: string = await addCase({ caseName: newCaseName.value.trim() })
    const newCase = {
      id: caseId,
      name: newCaseName.value.trim(),
    }
    emit('case-created', newCase)
    newCaseName.value = ''
  } catch (error) {
    ElMessage.error(
      getApiErrorMessage(error, { defaultServerMessage: 'Nie udało się utworzyć sprawy.' }),
    )
    console.error(error)
  }
}
</script>

<template>
  <el-card shadow="never" class="form-card" @click="inputRef?.focus()">
    <form class="case-form" @submit.prevent="createCase">
      <input
        id="case_name"
        ref="inputRef"
        v-model="newCaseName"
        name="case_name"
        placeholder="Utwórz nową sprawę..."
        required
        class="flex-grow-input"
      />
      <button type="submit" class="icon-btn">
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

input {
  border: none;
  background: transparent;
  outline: none;
  width: 100%;
  font-size: 1.1em;
}
</style>
