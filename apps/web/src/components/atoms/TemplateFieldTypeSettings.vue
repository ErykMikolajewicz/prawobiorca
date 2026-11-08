<script setup lang="ts">
import type { ApplicationFieldType } from '@/api/generated/model'

type Props = {
  fieldType: ApplicationFieldType
}

defineProps<Props>()

const pattern = defineModel<string | null>('pattern', { required: true })
const options = defineModel<string[]>('options', { required: true })
</script>

<template>
  <el-col v-if="fieldType === 'TEXT'" :span="12" :xs="24">
    <el-form-item label="Regex walidacji (opcjonalnie):">
      <el-input v-model="pattern" clearable placeholder="np. \d{6}" />
    </el-form-item>
  </el-col>

  <el-col v-else-if="fieldType === 'SELECT'" :span="12" :xs="24">
    <el-form-item label="Opcje listy:">
      <el-select
        v-model="options"
        multiple
        filterable
        allow-create
        default-first-option
        :reserve-keyword="false"
        placeholder="Wpisz opcję i naciśnij Enter"
      />
    </el-form-item>
  </el-col>
</template>
