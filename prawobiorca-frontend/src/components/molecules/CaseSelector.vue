<script setup lang="ts">
import { ref } from 'vue'
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import type { CaseData } from '@/api/generated/model'

const props = defineProps<{
  cases: Array<CaseData>
  selectedCaseId?: string
}>()

const emit = defineEmits<{
  (e: 'update:selectedCaseId', id: string): void
}>()

const authStore = useAuthStore()
const { isUserLogged } = storeToRefs(authStore)

const currentCaseId = ref(props.selectedCaseId || '')

const handleCaseSelect = (caseId: string) => {
  currentCaseId.value = caseId
  emit('update:selectedCaseId', caseId)
}
</script>

<template>
  <el-form-item v-if="isUserLogged" label="Bieżąca sprawa:">
    <el-select
      v-model="currentCaseId"
      placeholder="-- Wybierz z listy --"
      clearable
      @change="handleCaseSelect"
    >
      <el-option
        v-for="userCase in cases"
        :key="userCase.id"
        :label="userCase.name"
        :value="userCase.id"
      />
    </el-select>
  </el-form-item>
</template>
