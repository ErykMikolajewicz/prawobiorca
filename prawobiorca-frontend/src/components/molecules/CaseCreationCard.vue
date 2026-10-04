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
  <form class="case-form" @click="inputRef?.focus()" @submit.prevent="createCase">
    <button
      type="submit"
      class="icon-btn add-btn"
      aria-label="Utwórz sprawę"
      :disabled="isCreating"
    >
      <Add2RoundedIcon />
    </button>
    <el-input
      id="case_name"
      ref="inputRef"
      v-model="newCaseName"
      name="case_name"
      placeholder="Nowa sprawa..."
      required
      class="case-name-input"
    />
  </form>
</template>

<style scoped>
.case-form {
  display: flex;
  align-items: center;
  height: var(--el-menu-item-height);
  padding-left: var(--el-menu-base-level-padding);
  border-radius: 4px;
  cursor: text;

  &:hover {
    background-color: var(--el-menu-hover-bg-color);
  }
}

.add-btn {
  flex-shrink: 0;
  width: var(--el-menu-icon-width);
  margin-right: 5px;
  padding: 0;
}

.case-name-input {
  font-size: var(--el-menu-item-font-size);
}

.case-name-input :deep(.el-input__wrapper) {
  padding: 0;
  background: transparent;
  box-shadow: none;
}
</style>
