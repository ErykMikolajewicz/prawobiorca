<script setup lang="ts">
import type { ApplicationFieldType } from '@/api/generated/model'
import { DATE_VALUE_FORMAT } from '@/domain/applicationTemplates'

type Props = {
  fieldType: ApplicationFieldType
  options: string[]
}

defineProps<Props>()

const defaultValue = defineModel<string | null>({ required: true })
</script>

<template>
  <el-select v-if="fieldType === 'SELECT'" v-model="defaultValue" clearable placeholder="Brak">
    <el-option v-for="option in options" :key="option" :label="option" :value="option" />
  </el-select>
  <el-date-picker
    v-else-if="fieldType === 'DATE'"
    v-model="defaultValue"
    type="date"
    :format="DATE_VALUE_FORMAT"
    :value-format="DATE_VALUE_FORMAT"
    placeholder="Brak"
  />
  <el-input v-else v-model="defaultValue" clearable placeholder="Brak" />
</template>
