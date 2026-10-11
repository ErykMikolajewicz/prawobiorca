<script setup lang="ts">
import TemplateFieldDefaultValueInput from '@/components/atoms/TemplateFieldDefaultValueInput.vue'
import TemplateFieldTypeSettings from '@/components/atoms/TemplateFieldTypeSettings.vue'
import { fieldTypeOptions, type EditableTemplateField } from '@/domain/applicationTemplates'

const field = defineModel<EditableTemplateField>({ required: true })

function handleFieldTypeChange() {
  if (field.value.fieldType !== 'TEXT') {
    field.value.pattern = null
  }
  if (field.value.fieldType !== 'SELECT') {
    field.value.options = []
  }
  field.value.defaultValue = null
}
</script>

<template>
  <el-collapse-item :name="field.name">
    <template #title>
      <code class="field-name">{{ field.name }}</code>
    </template>

    <el-row :gutter="16">
      <el-col :span="12" :xs="24">
        <el-form-item label="Etykieta:">
          <el-input v-model="field.label" />
        </el-form-item>
      </el-col>

      <el-col :span="12" :xs="24">
        <el-form-item label="Typ:">
          <el-select v-model="field.fieldType" @change="handleFieldTypeChange">
            <el-option
              v-for="option in fieldTypeOptions"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-col>

      <TemplateFieldTypeSettings
        v-model:pattern="field.pattern"
        v-model:options="field.options"
        :field-type="field.fieldType"
      />

      <el-col :span="12" :xs="24">
        <el-form-item label="Wartość domyślna (opcjonalnie):">
          <TemplateFieldDefaultValueInput
            v-model="field.defaultValue"
            :field-type="field.fieldType"
            :options="field.options"
          />
        </el-form-item>
      </el-col>
    </el-row>

    <div class="field-flags">
      <el-checkbox v-model="field.required">Wymagane</el-checkbox>
      <el-checkbox v-model="field.passToAi">Przekaż do AI</el-checkbox>
    </div>
  </el-collapse-item>
</template>

<style scoped>
.field-name {
  color: var(--el-color-primary);
  font-weight: 600;
}

.field-flags {
  display: flex;
  gap: var(--app-space-xl);
}
</style>
