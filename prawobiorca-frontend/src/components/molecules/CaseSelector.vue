<script setup lang="ts">
import type { CaseData } from '@/api/generated/model'

defineProps<{
  cases: Array<CaseData>
}>()

const selectedCaseId = defineModel<string>('selectedCaseId')
</script>

<template>
  <el-form-item label="Bieżąca sprawa:">
    <el-select v-model="selectedCaseId" placeholder="-- Wybierz z listy --" clearable>
      <el-option
        v-for="userCase in cases"
        :key="userCase.id"
        :label="userCase.name"
        :value="userCase.id"
      />
    </el-select>
  </el-form-item>
</template>
